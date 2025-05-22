
Read file: prega_console.py

Read file: saints.json

Read file: bible_readings.json

Read file: saints_full_year.json

Read file: homepage.html
Here is a detailed README for the **SANTETIZZATORE V2** project, explaining every functionality and the structure of the application:

---

# SANTETIZZATORE V2

## Overview

**SANTETIZZATORE V2** is a comprehensive, interactive console application designed to help users explore the lives of saints, generate personalized prayers, and access Bible readings. The application integrates local data, online resources, and persistent storage to provide a rich spiritual experience. It is primarily written in Python and leverages JSON files, SQLite, and web APIs.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Detailed Functionality](#detailed-functionality)
  - [1. Prayer to Saints](#1-prayer-to-saints)
  - [2. Bible Readings](#2-bible-readings)
  - [3. Prayer History](#3-prayer-history)
  - [4. Saint of the Day](#4-saint-of-the-day)
- [Data Files](#data-files)
- [How to Run](#how-to-run)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [License](#license)

---

## Features

- **Interactive Console Menu**: Easy-to-use menu for navigating between functionalities.
- **Prayer Generation**: Select a saint, enter a request, and receive a personalized prayer.
- **Saint of the Day**: Fetches and suggests the Catholic saint of the day from an online feed.
- **Bible Readings**: Browse and search through a curated list of Bible passages.
- **Prayer History**: Stores and displays your recent prayers using SQLite.
- **Blessings**: Each prayer session ends with a random blessing.
- **Extensible Data**: Uses JSON files for saints and Bible readings, making it easy to update or expand.

---

## Project Structure

```
SANTETIZZATORE V2/
├── prega_console.py         # Main application script
├── saints.json              # List of saints and prayer templates
├── saints_full_year.json    # Full calendar of saints with bios
├── bible_readings.json      # Bible readings data
├── homepage.html            # (Optional) Web resource for saints
├── prayer_log.db            # SQLite database for prayer history (auto-created)
├── assets/                  # (Optional) Additional assets (e.g., fonts)
├── README.md                # Project documentation
└── ...                      # Other files
```

---

## Detailed Functionality

### 1. Prayer to Saints

- **Saint Selection**: Users can select a saint from a list (loaded from `saints.json`). Each saint has a name and specialty.
- **Saint of the Day Integration**: The app fetches the current day's saint from an online Catholic news feed and offers it as a default choice.
- **Request Input**: Users enter a personal prayer request.
- **Prayer Generation**: The app uses a set of templates to generate a personalized prayer, inserting the saint's name and the user's request.
- **Blessing**: After the prayer, a random blessing is displayed.
- **Logging**: Each prayer is saved in a local SQLite database (`prayer_log.db`) with a timestamp.

### 2. Bible Readings

- **Display Readings**: Shows a list of Bible readings, each with a category (e.g., Gospel, Old Testament), title, reference, and text.
- **Search**: Users can search readings by category or title.
- **Data Source**: Readings are loaded from `bible_readings.json`.

### 3. Prayer History

- **Recent Prayers**: Displays the last five prayers made by the user, including the saint, request, prayer text, and timestamp.
- **Persistence**: Uses SQLite for reliable, persistent storage.

### 4. Saint of the Day

- **Online Integration**: Fetches the saint of the day from the Catholic News Agency RSS feed.
- **Fallback**: If the online feed is unavailable, users can select a saint manually.
- **Full Calendar**: The `saints_full_year.json` file contains a comprehensive list of saints for every day of the year, including their names, feast days, and short bios.

---

## Data Files

- **saints.json**: Contains a list of saints, their specialties, and prayer templates. *(Note: If empty, the app may not function fully.)*
- **saints_full_year.json**: A detailed calendar of saints, with each entry including the day, name, festivity, and a short biography.
- **bible_readings.json**: An array of Bible readings, each with a category, title, reference, and text.

---

## How to Run

1. **Install Python 3.7+** if not already installed.
2. **Install dependencies** (see below).
3. **Ensure data files** (`saints.json`, `saints_full_year.json`, `bible_readings.json`) are present in the project directory.
4. **Run the application**:
   ```sh
   python prega_console.py
   ```

---

## Dependencies

- Python 3.7+
- Standard libraries: `json`, `random`, `sqlite3`, `os`, `requests`, `feedparser`
- Install external dependencies:
  ```sh
  pip install requests feedparser
  ```

---

## Troubleshooting

- **Missing Data Files**: Ensure all required JSON files are present and correctly formatted.
- **Database Issues**: The app creates `prayer_log.db` automatically. If you encounter issues, try deleting the file to reset history.
- **Internet Connection**: Required for fetching the saint of the day.
- **Encoding**: Data files should be UTF-8 encoded.

---

## Credits

- Developed by [Ora Pro Nobis].
- Uses data from Catholic News Agency and other open resources.

---

## License

[Specify your license here, e.g., MIT, GPL, etc.]

---

**SANTETIZZATORE V2** is designed to enrich your spiritual journey with daily inspiration, personalized prayers, and easy access to sacred texts. 
Contributions and suggestions are welcome!

---

