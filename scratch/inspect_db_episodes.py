import sqlite3
import json

conn = sqlite3.connect('data/anime.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables in anime.db:", tables)

for t in tables:
    t_name = t[0]
    c.execute(f"PRAGMA table_info({t_name})")
    cols = [r[1] for r in c.fetchall()]
    print(f"Table '{t_name}' columns: {cols}")
    c.execute(f"SELECT COUNT(*) FROM {t_name}")
    print(f"Table '{t_name}' rows count: {c.fetchone()[0]}")

# Let's inspect titles in the main table
table_name = tables[0][0]
c.execute(f"SELECT key, title_ru, data_json FROM {table_name} WHERE key IN ('naruto-shippuuden', 'naruto', 'bleach', 'one-piece', 'jujutsu-kaisen')")
for row in c.fetchall():
    key, title, data_raw = row
    d = json.loads(data_raw)
    eps = d.get('episodes')
    print(f"\n==================== {title} ({key}) ====================")
    if not eps:
        print("   episodes: None")
    elif isinstance(eps, dict):
        items = eps.get('items', [])
        print(f"   episodes dict count: {len(items)}, keys: {list(eps.keys())}")
        if items:
            print("   Sample ep 1:", items[0])
            if len(items) > 10:
                print("   Sample ep 10:", items[9])
    elif isinstance(eps, list):
        print(f"   episodes list count: {len(eps)}")
        if eps:
            print("   Sample ep 1:", eps[0])
