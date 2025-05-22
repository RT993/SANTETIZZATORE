import json
import random
import sqlite3
import os
import requests
import feedparser

# Load data from JSON
DATA_FILE = 'saints.json'
DB_FILE = 'prayer_log.db'

def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def select_saint(saints):
    print("\nScegli un santo:")
    for i, s in enumerate(saints):
        print(f"{i+1}. {s['name']} ({s['specialty']})")
    while True:
        try:
            choice = int(input("Inserisci il numero del santo scelto: ")) - 1
            if 0 <= choice < len(saints):
                return saints[choice]
        except ValueError:
            pass
        print("Scelta non valida. Riprova.")

def get_request():
    return input("\nCosa è la tua richiesta? ")

def generate_prayer(templates, saint_name, user_request):
    template = random.choice(templates)
    return template.format(saint=saint_name, request=user_request)

def log_prayer(saint, request, prayer):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prayers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        saint TEXT,
        request TEXT,
        prayer TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('INSERT INTO prayers (saint, request, prayer) VALUES (?, ?, ?)', (saint, request, prayer))
    conn.commit()
    conn.close()

def show_history():
    if not os.path.exists(DB_FILE):
        print("\nNessuna storia di preghiera ancora.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT saint, request, prayer, timestamp FROM prayers ORDER BY timestamp DESC LIMIT 5')
    rows = c.fetchall()
    if rows:
        print("\nPreghiere recenti:")
        for row in rows:
            print(f"[{row[3]}] A {row[0]}: {row[1]}\n  Preghiera: {row[2]}\n")
    else:
        print("\nNessuna storia di preghiera ancora.")
    conn.close()

def get_saint_of_the_day():
    feed_url = "https://feeds.feedburner.com/catholicnewsagency/saintoftheday"
    try:
        resp = requests.get(feed_url, timeout=10)
        feed = feedparser.parse(resp.content)
        if not feed.entries:
            return None
        entry = feed.entries[0]
        saint_name = entry.title
        # Optionally, you can also get description or image if needed
        return saint_name
    except Exception as e:
        return None

# Sample data structure for Bible readings
bible_readings = [
    {
        "category": "Vangelo",
        "title": "The Beatitudes",
        "reference": "Matthew 5:1-12",
        "text": None
    },
    {
        "category": "Vangelo",
        "title": "The Good Samaritan",
        "reference": "Luke 10:25-37",
        "text": None
    },
    {
        "category": "Antico Testamento",
        "title": "The Lord is my Shepherd",
        "reference": "Psalm 23",
        "text": None
    },
    {
        "category": "Lettere agli Apostoli",
        "title": "Love is patient",
        "reference": "1 Corinthians 13:1-13",
        "text": None
    },
]

def display_readings(readings):
    for reading in readings:
        print(f"[{reading['category']}] {reading['title']} ({reading['reference']})")


def search_readings(readings, query):
    query = query.lower()
    results = [r for r in readings if query in r['category'].lower() or query in r['title'].lower()]
    return results

def load_bible_readings(filename='bible_readings.json'):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def letture_bibliche_menu():
    readings = load_bible_readings()
    display_readings(readings)
    input("\nPremi Invio per tornare al menu principale...")

def main():
    data = load_data()
    saints = data['saints']
    templates = data['prayer_templates']
    blessings = data['blessings']

    while True:
        print("\nBenvenuto in Prega!")
        print("1. Preghiera ai Santi")
        print("2. Letture Bibliche")
        print("3. Mostra storia preghiere")
        print("4. Esci")
        choice = input("Scegli un'opzione: ").strip()
        if choice == '1':
            # Saint of the day integration
            saint_of_day_name = get_saint_of_the_day()
            saint_of_day = None
            if saint_of_day_name:
                print(f"\nSanto del Giorno: {saint_of_day_name}")
                for s in saints:
                    if s['name'].lower() in saint_of_day_name.lower():
                        saint_of_day = s
                        break
                use_saint_of_day = input("Vorresti usare il Santo del Giorno? (y/n): ").strip().lower()
                if use_saint_of_day == 'y' and saint_of_day:
                    saint = saint_of_day
                else:
                    saint = select_saint(saints)
            else:
                saint = select_saint(saints)
            request = get_request()
            prayer = generate_prayer(templates, saint['name'], request)
            print("\nLa tua preghiera:\n" + prayer)
            log_prayer(saint['name'], request, prayer)
            print("\nBenedizione:", random.choice(blessings))
        elif choice == '2':
            letture_bibliche_menu()
        elif choice == '3':
            show_history()
        elif choice == '4':
            print("Arrivederci!")
            break
        else:
            print("Scelta non valida. Riprova.")

if __name__ == "__main__":
    main()
    print("All Bible Readings:")
    display_readings(bible_readings)
    print("\nSearch for 'vangelo':")
    display_readings(search_readings(bible_readings, 'vangelo'))
    print("\nSearch for 'love':")
    display_readings(search_readings(bible_readings, 'love')) 