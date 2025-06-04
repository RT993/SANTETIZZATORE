# Saint of the Day App – Android Port (Kivy)

## Overview
This project is a port of the original console-based "Saint of the Day" Python application to Android, using the Kivy framework. The app displays the saint associated with the current day, leveraging a JSON file (`saints_full_year.json`) as its data source. The Android version features a touchscreen-friendly graphical user interface (GUI) and is packaged as an APK for easy installation on Android devices.

---
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

- Developed by [Your Name/Team].
- Uses data from Catholic News Agency and other open resources.

---

## License

[Specify your license here, e.g., MIT, GPL, etc.]

---

**SANTETIZZATORE V2** is designed to enrich your spiritual journey with daily inspiration, personalized prayers, and easy access to sacred texts. Contributions and suggestions are welcome!

---

If you need a section expanded or want to include usage examples, screenshots, or more technical details, let me know!


## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Implementation Details](#implementation-details)
- [How to Run Locally (Desktop)](#how-to-run-locally-desktop)
- [Packaging for Android](#packaging-for-android)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)

---

## Features
- **Touchscreen-friendly GUI**: Built with Kivy for seamless interaction on Android devices.
- **Saint of the Day**: Displays the saint for the current date, based on a JSON data file.
- **Simple, clean interface**: One button to fetch and display today's saint.
- **Cross-platform**: Can be run on desktop (Windows, macOS, Linux) and Android.

---

## Project Structure
```
SANTETIZZATORE V2/
├── main.py                  # Kivy app entry point
├── saint_of_the_day.py      # Core logic for fetching today's saint
├── saints_full_year.json    # Data file mapping dates to saints
├── buildozer.spec           # Buildozer configuration for Android packaging
├── README.md                # This file
└── ...                      # Other assets and files
```

---

## Implementation Details

### 1. Refactoring Core Logic
- The saint-fetching logic was separated into `saint_of_the_day.py` as a reusable class (`SaintOfTheDay`).
- The class loads the JSON data and provides a method to fetch the saint for the current date.

**saint_of_the_day.py**
```python
import json
from datetime import datetime

class SaintOfTheDay:
    def __init__(self, json_file):
        with open(json_file, "r") as f:
            self.saints = json.load(f)

    def get_today_saint(self):
        today = datetime.now().strftime("%m-%d")
        return self.saints.get(today, "No saint found for today.")
```

### 2. Creating the Kivy GUI
- The GUI is built in `main.py` using Kivy's `BoxLayout`, `Label`, and `Button` widgets.
- The app displays a label and a button. When the button is pressed, it updates the label with today's saint.

**main.py**
```python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from saint_of_the_day import SaintOfTheDay

class SaintApp(App):
    def build(self):
        self.saint = SaintOfTheDay("saints_full_year.json")
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Press the button to see today's saint")
        btn = Button(text="Show Today's Saint")
        btn.bind(on_press=self.show_saint)
        layout.add_widget(self.label)
        layout.add_widget(btn)
        return layout

    def show_saint(self, instance):
        saint = self.saint.get_today_saint()
        self.label.text = f"Today's Saint: {saint}"

if __name__ == "__main__":
    SaintApp().run()
```

### 3. Testing on Desktop
- The app can be run on any desktop OS with Python and Kivy installed:
  ```sh
  pip install kivy
  python main.py
  ```

### 4. Packaging for Android
- **Buildozer** is used to package the app for Android.
- Steps:
  1. Install Buildozer: `pip install buildozer`
  2. Initialize: `buildozer init` (creates `buildozer.spec`)
  3. Edit `buildozer.spec` to include `saint_of_the_day.py` and `saints_full_year.json` in the `source.include_exts` and `source.include_patterns` fields.
  4. Build the APK: `buildozer -v android debug`
  5. Deploy to device: `buildozer android deploy run`

**Note:** Buildozer requires Linux or WSL (Windows Subsystem for Linux) for Android builds.

---

## Dependencies
- Python 3.7+
- Kivy
- Buildozer (for Android packaging)
- JSON data file (`saints_full_year.json`)

Install dependencies for desktop testing:
```sh
pip install kivy
```

---

## Troubleshooting
- **Buildozer errors:** Ensure you are running on Linux/WSL and have all Android SDK/NDK dependencies installed. See [Buildozer documentation](https://buildozer.readthedocs.io/en/latest/).
- **File not found:** Make sure `saints_full_year.json` is included in your project and referenced correctly in both Python and `buildozer.spec`.
- **Touchscreen issues:** Kivy is designed for touch, but test on your device to ensure the UI is responsive.

---

## Credits
- Original console app by [Your Name].
- Kivy framework: https://kivy.org/
- Buildozer: https://buildozer.readthedocs.io/

---

## License
[Specify your license here] 