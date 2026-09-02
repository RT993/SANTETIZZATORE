# SANTETIZZATORE

A PyQt5 desktop app (designed with a touchscreen/infotainment-style UI) for exploring saints, generating personalized prayers, reading daily Bible passages, and following Vatican news.

The application lives entirely in [`SANTETIZZATORE V2/`](./SANTETIZZATORE%20V2) — that is the current, maintained version.

## Features

- **Santo del giorno**: shows the saint associated with the current date, pulled from `saints.json`.
- **Prega**: pick a saint and a request category, get a generated prayer and a saint's "reply".
- **Letture Bibliche**: a Bible reading of the day, served from a local SQLite database (`bible_readings.db`).
- **Dal Vaticano**: latest news from the Vatican News RSS feed, opened in an in-app browser.
- **Promemoria**: prayer reminder times shown on a card with an animated clock.

## Project structure

```
SANTETIZZATORE V2/
├── main.py                    # PyQt5 GUI app (entry point)
├── migrate_bible_readings.py  # One-off script: rebuilds bible_readings.db from bible_readings.json
├── generate_gifs.py           # One-off script: regenerates the loading/halo GIF assets
├── saints.json                # Saints calendar (day -> name, festivity, bio)
├── bible_readings.json        # Bible readings source data
├── bible_readings.db          # SQLite database used by the app (pre-built from bible_readings.json)
├── assets/                    # Images, fonts, GIFs used by the UI
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
