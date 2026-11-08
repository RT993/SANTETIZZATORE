"""
Scrapes santiebeati.it for one principal saint per calendar day (366 days,
including Feb 29), producing saints.json with a real name, bio and portrait
for each day, plus the matching image files under assets/saints/.

Source: https://www.santiebeati.it/{MM}/{DD}/ lists every saint venerated on
that date; the first entry on the page is the site's featured "Santo del
Giorno" for that date (verified against https://www.santiebeati.it/ilsantodelgiorno.txt
and against the pre-existing saints.json, which already had the right saint
first for every day it covered). That entry links to a /dettaglio/<id> page
carrying the actual biography and a portrait thumbnail.

Usage:
    python3 scrape_saints.py [--start MM-DD] [--delay SECONDS]

Safe to interrupt and re-run: days already present in the output JSON are
skipped, so progress is never lost.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(BASE_DIR, "saints.json")
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "saints")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SantetizzatoreScraper/1.0)"}
TIMEOUT = 20

# Thumbnail the site serves in place of a real photo when none exists.
PLACEHOLDER_IMAGE_MD5 = "a943672a32297727bab01c3e76977550"
MIN_IMAGE_BYTES = 2000

ITALIAN_MONTHS = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]

DAY_ENTRY_RE = re.compile(
    r'<a href="/dettaglio/(\d+)" title="[^"]*">'
    r'<FONT SIZE="-2">([^<]*)</FONT>\s*'
    r'<FONT SIZE="-1"><b>([^<]*)</b></FONT></a>\s*&nbsp;'
    r'<FONT SIZE="-2" COLOR="#FFFFFF">([^<]*)</FONT>&nbsp;',
    re.IGNORECASE,
)

IMAGE_SRC_RE = re.compile(
    r'<img\s+src="(/immagini/Thumbs/\d+/[^"]+)"', re.IGNORECASE
)

# The main content block: from the birth/death line down to the audio
# players (present on every detail page, right after Martirologio Romano).
CONTENT_BLOCK_RE = re.compile(
    r'<TD BGCOLOR="#333399">(.*?)(?:<BR><CENTER>|$)', re.IGNORECASE | re.DOTALL
)

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]+")
BLANKLINES_RE = re.compile(r"\n\s*\n+")

FIELD_LABELS = ["Patronato", "Etimologia", "Emblema", "Martirologio Romano"]


def all_days(start=None):
    days = []
    for month in range(1, 13):
        max_day = 29 if month == 2 else (30 if month in (4, 6, 9, 11) else 31)
        for day in range(1, max_day + 1):
            days.append((month, day))
    if start:
        m, d = start
        days = [x for x in days if x >= (m, d)]
    return days


def day_key(month, day):
    return f"{month:02d}-{day:02d}"


def festivity_str(month, day):
    return f"{day} {ITALIAN_MONTHS[month - 1]}"


def html_to_text(fragment):
    text = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text)
    text = BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def extract_bio(detail_html):
    block_match = CONTENT_BLOCK_RE.search(detail_html)
    if not block_match:
        return ""
    block = block_match.group(1)

    # Split the block on the known field labels so we can pull out the
    # free-form narrative (before any label) and the Martirologio Romano
    # entry (after its label), regardless of which optional fields
    # (Patronato / Etimologia / Emblema) are present for this saint.
    label_pattern = "|".join(re.escape(lbl) for lbl in FIELD_LABELS)
    split_re = re.compile(
        r'<FONT\s+COLOR="#FF3300">\s*(' + label_pattern + r'):\s*</FONT>',
        re.IGNORECASE,
    )
    parts = split_re.split(block)
    # parts alternates: [pre-text, label, text, label, text, ...]
    raw_narrative = html_to_text(parts[0])
    # Drop the leading "(Papa dal ...)"-style admin line and the
    # birth/death line, keeping only actual prose paragraphs.
    narrative_lines = [
        line for line in raw_narrative.split("\n\n")
        if line and not line.startswith("(") and len(line) > 20
    ]
    narrative = "\n\n".join(narrative_lines)

    martirologio = ""
    for i in range(1, len(parts), 2):
        if parts[i].strip().lower() == "martirologio romano":
            martirologio = html_to_text(parts[i + 1])
            break

    bio_parts = [p for p in (narrative, martirologio) if p]
    if bio_parts:
        return "\n\n".join(bio_parts)
    # A handful of very obscure entries have nothing but a short
    # death-date stub (e.g. "+ 29 febbraio 1264") - better than nothing.
    return raw_narrative.strip()


def fetch(session, url):
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    # The server's Content-Type header omits a charset, so requests falls
    # back to Latin-1 per the HTTP spec default even though the actual
    # bytes are UTF-8 - decode explicitly to avoid mojibake.
    resp.encoding = "utf-8"
    return resp.text


def scrape_day(session, month, day):
    key = day_key(month, day)
    day_url = f"https://www.santiebeati.it/{month:02d}/{day:02d}/"
    day_html = fetch(session, day_url)
    match = DAY_ENTRY_RE.search(day_html)
    if not match:
        print(f"  [{key}] no saint found on day page, skipping")
        return None

    saint_id, prefix, name, subtitle = match.groups()
    full_name = html.unescape(f"{prefix} {name}".strip())
    subtitle = html.unescape(subtitle.strip())

    detail_url = f"https://www.santiebeati.it/dettaglio/{saint_id}"
    detail_html = fetch(session, detail_url)

    bio = extract_bio(detail_html)
    if not bio:
        bio = "Biografia non disponibile."

    image_rel_path = None
    img_match = IMAGE_SRC_RE.search(detail_html)
    if img_match:
        image_url = "https://www.santiebeati.it" + img_match.group(1)
        try:
            img_resp = session.get(image_url, headers=HEADERS, timeout=TIMEOUT)
            img_resp.raise_for_status()
            content = img_resp.content
            if len(content) >= MIN_IMAGE_BYTES and hashlib.md5(content).hexdigest() != PLACEHOLDER_IMAGE_MD5:
                ext = os.path.splitext(urllib.parse.urlparse(image_url).path)[1] or ".jpg"
                os.makedirs(IMAGES_DIR, exist_ok=True)
                out_path = os.path.join(IMAGES_DIR, f"{key}{ext.lower()}")
                with open(out_path, "wb") as f:
                    f.write(content)
                image_rel_path = os.path.join("assets", "saints", f"{key}{ext.lower()}")
        except requests.RequestException as e:
            print(f"  [{key}] image download failed: {e}")

    return {
        "day": key,
        "name": full_name,
        "subtitle": subtitle,
        "festivity": festivity_str(month, day),
        "bio": bio,
        "image": image_rel_path,
        "source_id": int(saint_id),
        "source_url": detail_url,
    }


def load_existing():
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data and "source_id" in data[0]:
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
    parser.add_argument("--start", help="Resume from this MM-DD day (inclusive)")
    parser.add_argument("--delay", type=float, default=0.4, help="Seconds between requests")
    args = parser.parse_args()

    start = None
    if args.start:
        m, d = args.start.split("-")
        start = (int(m), int(d))

    entries = load_existing()
    session = requests.Session()

    for month, day in all_days(start):
        key = day_key(month, day)
        if key in entries:
            continue
        try:
            entry = scrape_day(session, month, day)
        except requests.RequestException as e:
            print(f"  [{key}] request failed: {e} - stopping, re-run to resume")
            save(entries)
            sys.exit(1)
        if entry:
            entries[key] = entry
            print(f"  [{key}] {entry['name']}" + (" (photo)" if entry["image"] else " (no photo)"))
        save(entries)
        time.sleep(args.delay)

    print(f"Done: {len(entries)}/366 days saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
