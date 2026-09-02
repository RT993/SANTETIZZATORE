import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load readings from JSON
with open(os.path.join(BASE_DIR, 'bible_readings.json'), 'r', encoding='utf-8') as f:
    readings = json.load(f)

# Connect to SQLite DB
conn = sqlite3.connect(os.path.join(BASE_DIR, 'bible_readings.db'))
c = conn.cursor()

# Insert readings
for r in readings:
    c.execute('INSERT INTO readings (category, title, reference, text) VALUES (?, ?, ?, ?)',
              (r['category'], r['title'], r['reference'], r['text']))

conn.commit()
conn.close()
print('Migration complete.') 