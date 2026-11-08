"""
Scrapes chiesacattolica.it (the Italian Bishops' Conference's official
liturgy site) for one Gospel reading per calendar day (365 days),
producing bible_readings.json keyed by MM-DD - same shape and lookup
pattern as saints.json, so the reading is stable across years instead
of drifting via a day-of-year/leap-year-sensitive row offset (the old
SQLite-based lookup showed every date after Feb 29 off-by-one for the
rest of any leap year).

Source: https://www.chiesacattolica.it/liturgia-del-giorno/?data-liturgia=YYYYMMDD
gives that date's actual Mass readings; we take the Gospel section
(reference, short pericope subtitle, and full text) since weekday
Gospel readings follow a fixed annual cycle (unlike Sunday readings
and first readings, which vary by liturgical year A/B/C or I/II),
making it the most evergreen section to key by plain MM-DD. Sundays
will still show whichever year's Gospel we scraped rather than the
liturgically "correct" one for future years - a reasonable trade-off
for a devotional app that isn't for official liturgical use.

Usage:
    python3 scrape_bible_readings.py [--year YYYY] [--start MM-DD] [--delay SECONDS]

Safe to interrupt and re-run: days already present in the output JSON
are skipped, so progress is never lost.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(BASE_DIR, "bible_readings.json")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SantetizzatoreScraper/1.0)"}
TIMEOUT = 20

VANGELO_SECTION_RE = re.compile(
    r'<h2 class="cci-liturgia-giorno-section-title">Vangelo</h2>(.*?)'
    r'(?:<h2 class="cci-liturgia-giorno-section-title">|$)',
    re.DOTALL,
)
SUBTITLE_RE = re.compile(
    r'<h3 class="cci-liturgia-giorno-section-subtitle">(.*?)</h3>', re.DOTALL
)
CONTENT_DIV_RE = re.compile(
    r'<div class="cci-liturgia-giorno-section-content">(.*?)</div>', re.DOTALL
)

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]+")
BLANKLINES_RE = re.compile(r"\n\s*\n+")
PAROLA_RE = re.compile(r"^Parola (del|di) (Signore|Dio)\.?$", re.IGNORECASE)


def html_to_text(fragment):
    # <br> tags sometimes carry inline style attributes (content pasted
    # from a rich-text editor), so match any attributes, not just a bare
    # <br/>.
    text = re.sub(r"(?i)<br\b[^>]*>", "\n", fragment)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = WS_RE.sub(" ", text)
    text = BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def all_days(year, start=None):
    d = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    days = []
    while d <= end:
        days.append((d.month, d.day))
        d += datetime.timedelta(days=1)
    if start:
        m, dd = start
        days = [x for x in days if x >= (m, dd)]
    return days


def day_key(month, day):
    return f"{month:02d}-{day:02d}"


def fetch(session, url):
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def scrape_day(session, year, month, day):
    key = day_key(month, day)
    url = f"https://www.chiesacattolica.it/liturgia-del-giorno/?data-liturgia={year}{month:02d}{day:02d}"
    page_html = fetch(session, url)

    if "Nessun Contenuto Trovato" in page_html:
        print(f"  [{key}] not yet published on the site, skipping")
        return None

    section_match = VANGELO_SECTION_RE.search(page_html)
    if not section_match:
        print(f"  [{key}] no Vangelo section found, skipping")
        return None
    block = section_match.group(1)

    subtitle_match = SUBTITLE_RE.search(block)
    title = html_to_text(subtitle_match.group(1)) if subtitle_match else "Vangelo del giorno"

    content_match = CONTENT_DIV_RE.search(block)
    if not content_match:
        print(f"  [{key}] no content div found, skipping")
        return None
    text = html_to_text(content_match.group(1))

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        print(f"  [{key}] empty content, skipping")
        return None

    # lines[0] = "Dal Vangelo secondo Luca", lines[1] = citation e.g. "Lc 5,1-11"
    evangelist_match = re.match(r"Dal Vangelo secondo (\w+)", lines[0])
    evangelist = evangelist_match.group(1) if evangelist_match else ""
    citation = lines[1] if len(lines) > 1 else ""
    verse_match = re.search(r"\d.*", citation)
    verse = verse_match.group(0) if verse_match else citation
    reference = f"{evangelist} {verse}".strip()

    body_lines = lines[2:]
    if body_lines and PAROLA_RE.match(body_lines[-1]):
        body_lines = body_lines[:-1]
    body = "\n".join(body_lines).strip()
    if not body:
        print(f"  [{key}] empty body, skipping")
        return None

    return {
        "day": key,
        "category": "Vangelo",
        "title": title,
        "reference": reference,
        "text": body,
        "source_url": url,
    }


def load_existing():
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data and "day" in data[0]:
                return {entry["day"]: entry for entry in data}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save(entries_by_day):
    ordered = [entries_by_day[k] for k in sorted(entries_by_day)]
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025,
                         help="Which year's liturgical calendar to scrape (readings are stored by MM-DD, not tied to this year). "
                              "Must be a year the site has already fully published - the current and future months are not yet "
                              "available (the page returns 'Nessun Contenuto Trovato' for unpublished dates).")
    parser.add_argument("--start", help="Resume from this MM-DD day (inclusive)")
    parser.add_argument("--delay", type=float, default=0.4, help="Seconds between requests")
    args = parser.parse_args()

    start = None
    if args.start:
        m, d = args.start.split("-")
        start = (int(m), int(d))

    entries = load_existing()
    session = requests.Session()

    for month, day in all_days(args.year, start):
        key = day_key(month, day)
        if key in entries:
            continue
        try:
            entry = scrape_day(session, args.year, month, day)
        except requests.RequestException as e:
            print(f"  [{key}] request failed: {e} - stopping, re-run to resume")
            save(entries)
            sys.exit(1)
        if entry:
            entries[key] = entry
            print(f"  [{key}] {entry['title']} ({entry['reference']})")
        save(entries)
        time.sleep(args.delay)

    print(f"Done: {len(entries)}/365 days saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
