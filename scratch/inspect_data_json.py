import sqlite3
import json

conn = sqlite3.connect('data/anime.db')
cur = conn.cursor()
cur.execute("SELECT key, length(data_json), data_json FROM titles LIMIT 3")
for row in cur.fetchall():
    key, l, data_raw = row
    data = json.loads(data_raw)
    print(f"Key: {key}, size: {l/1024:.1f} KB")
    print("Keys inside data:", list(data.keys()))
    if "sources" in data:
        print("Sources:", {k: len(str(v)) for k, v in data["sources"].items()})
