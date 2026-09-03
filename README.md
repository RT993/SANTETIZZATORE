# SANTETIZZATORE

A PyQt5 desktop app (designed with a touchscreen/infotainment-style UI) for exploring saints, generating personalized prayers, reading daily Bible passages, and following Vatican news.

The application lives entirely in [`SANTETIZZATORE V2/`](./SANTETIZZATORE%20V2) — that is the current, maintained version.

## Features

- **Santo del giorno**: shows the saint associated with the current date, pulled from `saints.json`.
- **Prega**: pick a saint and a request category, get a generated prayer and a saint's "reply".
- **Letture Bibliche**: a Bible reading of the day, pulled from `bible_readings.json`.
- **Dal Vaticano**: latest news from the Vatican News RSS feed, opened in an in-app browser.
- **Promemoria**: prayer reminder times shown on a card with an animated clock.

## Project structure

```
SANTETIZZATORE V2/
├── main.py                     # PyQt5 GUI app (entry point)
├── scrape_saints.py             # Scraper: (re)generates saints.json + assets/saints/ from santiebeati.it
├── scrape_bible_readings.py     # Scraper: (re)generates bible_readings.json from chiesacattolica.it
├── generate_gifs.py             # One-off script: regenerates the loading/halo GIF assets
├── saints.json                  # Saints calendar (day -> name, festivity, bio)
├── bible_readings.json          # Bible readings calendar (day -> category, title, reference, text)
├── assets/                      # Images, fonts, GIFs used by the UI
│   └── saints/                  # Per-day saint portraits (scraped)
└── requirements.txt
```

## How to run

```sh
cd "SANTETIZZATORE V2"
pip install -r requirements.txt
python main.py
```

## Dependencies

See `SANTETIZZATORE V2/requirements.txt` (PyQt5, feedparser, requests).

## License

[Specify your license here, e.g., MIT, GPL, etc.]
