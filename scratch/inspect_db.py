import sqlite3

conn = sqlite3.connect('data/anime.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(titles)")
cols = [r[1] for r in cur.fetchall()]
print("Columns:", cols)

for col in cols:
    try:
        cur.execute(f"SELECT SUM(length(CAST({col} AS BLOB))) FROM titles")
        size = cur.fetchone()[0] or 0
        print(f"  {col}: {size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"  {col}: {e}")
