import json
import sqlite3

# Load readings from JSON
with open('SANTETIZZATORE V2/bible_readings.json', 'r', encoding='utf-8') as f:
    readings = json.load(f)

# Connect to SQLite DB
conn = sqlite3.connect('SANTETIZZATORE V2/bible_readings.db')
c = conn.cursor()

# Insert readings
for r in readings:
    c.execute('INSERT INTO readings (category, title, reference, text) VALUES (?, ?, ?, ?)',
              (r['category'], r['title'], r['reference'], r['text']))

conn.commit()
conn.close()
print('Migration complete.') 