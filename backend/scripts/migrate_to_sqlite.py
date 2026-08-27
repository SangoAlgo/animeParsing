"""Migration script: imports all records from data/anime.json into data/anime.db and verifies queries."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import DB_PATH, get_filter_facets, init_db, query_titles, upsert_title

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "anime.json")


def migrate():
    print(f"=== Initializing SQLite Database at: {DB_PATH} ===")
    init_db(DB_PATH)

    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} does not exist!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    titles = data.get("titles", [])
    print(f"Found {len(titles)} titles in {DATA_FILE}. Migrating...")

    for i, t in enumerate(titles, 1):
        key = t.get("key")
        title_id = upsert_title(t, DB_PATH)
        print(f"  [{i}/{len(titles)}] Migrated '{key}' -> ID {title_id}")

    print("\n=== Migration Complete! Running Verifications ===")

    # 1. Test total count
    res_all = query_titles(limit=50)
    print(f"Total titles in DB: {res_all['total']}")

    # 2. Test FTS Search
    res_search = query_titles(q="титан")
    print(f"FTS search 'титан': found {res_search['total']} titles: {[t['key'] for t in res_search['items']]}")

    # 3. Test Genre filter
    res_genre = query_titles(genres=["Экшен", "Сёнен"])
    print(f"Genre filter ['Экшен', 'Сёнен']: found {res_genre['total']} titles: {[t['key'] for t in res_genre['items']]}")

    # 4. Test Kodik Voiceover filter
    res_vo = query_titles(voiceovers=["AniLibria"])
    print(f"Voiceover filter ['AniLibria']: found {res_vo['total']} titles: {[t['key'] for t in res_vo['items']]}")

    # 5. Test Facets
    facets = get_filter_facets()
    print(f"\nFacets summary:")
    print(f"  - Top Genres: {[g['name'] + ' (' + str(g['count']) + ')' for g in facets['genres'][:6]]}")
    print(f"  - Top Studios: {[s['name'] + ' (' + str(s['count']) + ')' for s in facets['studios'][:5]]}")
    print(f"  - Top Voiceovers: {[v['name'] + ' (' + str(v['count']) + ')' for v in facets['voiceovers'][:5]]}")
    print(f"  - Years: {facets['years']}")


if __name__ == "__main__":
    migrate()
