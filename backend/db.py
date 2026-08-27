"""SQLite Database Layer with WAL Mode, Full-Text Search (FTS5), and Relational Indexing.

Features:
- Schema with indexes on key, format, status, year, score, shikimori_id
- Relational tables for genres, animation studios, and Kodik voiceover translations
- FTS5 virtual table for lightning-fast full-text search across Russian, English, Japanese names and descriptions
- Flexible query builder with multi-facet filtering and sorting
"""
from __future__ import annotations

import glob
import gzip
import json
import logging
import os
import shutil
import sqlite3
import time
from typing import Any

log = logging.getLogger("db")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "anime.db")


def ensure_db_exists(db_path: str = DB_PATH) -> None:
    """Checks if database file exists; if not, attempts to unpack from compressed chunks."""
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        return
    data_dir = os.path.dirname(db_path)
    parts = sorted(glob.glob(f"{db_path}.gz.*"))
    if not parts:
        single_gz = f"{db_path}.gz"
        if os.path.exists(single_gz):
            parts = [single_gz]
    if parts:
        print(f"Unpacking SQLite database from {len(parts)} compressed chunk(s)...")
        temp_gz = os.path.join(data_dir, "anime.db.gz.tmp")
        try:
            with open(temp_gz, "wb") as f_out:
                for p in parts:
                    with open(p, "rb") as f_in:
                        shutil.copyfileobj(f_in, f_out)
            with gzip.open(temp_gz, "rb") as f_in:
                with open(db_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print("Database unpacked successfully!")
        finally:
            if os.path.exists(temp_gz):
                os.remove(temp_gz)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    ensure_db_exists(db_path)
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes the database schema, indexes, and FTS5 tables."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        title_ru TEXT,
        title_en TEXT,
        title_ja TEXT,
        shikimori_id INTEGER,
        anilist_id INTEGER,
        mal_id INTEGER,
        format TEXT,
        format_ru TEXT,
        status TEXT,
        status_ru TEXT,
        year INTEGER,
        season TEXT,
        episodes_total INTEGER,
        episodes_aired INTEGER,
        duration_min INTEGER,
        score_avg REAL,
        score_shikimori REAL,
        score_anilist REAL,
        age_rating TEXT,
        age_rating_ru TEXT,
        poster_url TEXT,
        banner_url TEXT,
        description_ru TEXT,
        data_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_titles_key ON titles(key);
    CREATE INDEX IF NOT EXISTS idx_titles_year ON titles(year);
    CREATE INDEX IF NOT EXISTS idx_titles_score_avg ON titles(score_avg);
    CREATE INDEX IF NOT EXISTS idx_titles_format ON titles(format);
    CREATE INDEX IF NOT EXISTS idx_titles_status ON titles(status);
    CREATE INDEX IF NOT EXISTS idx_titles_shikimori ON titles(shikimori_id);

    -- Relational table for genres
    CREATE TABLE IF NOT EXISTS title_genres (
        title_id INTEGER NOT NULL,
        genre TEXT NOT NULL,
        PRIMARY KEY (title_id, genre),
        FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_title_genres_genre ON title_genres(genre);

    -- Relational table for animation studios
    CREATE TABLE IF NOT EXISTS title_studios (
        title_id INTEGER NOT NULL,
        studio TEXT NOT NULL,
        PRIMARY KEY (title_id, studio),
        FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_title_studios_studio ON title_studios(studio);

    -- Relational table for Kodik voiceover translations
    CREATE TABLE IF NOT EXISTS title_translations (
        title_id INTEGER NOT NULL,
        studio_name TEXT NOT NULL,
        type TEXT NOT NULL,
        episodes_count INTEGER DEFAULT 0,
        PRIMARY KEY (title_id, studio_name, type),
        FOREIGN KEY (title_id) REFERENCES titles(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_title_trans_name ON title_translations(studio_name);

    -- FTS5 Full-Text Search Virtual Table
    CREATE VIRTUAL TABLE IF NOT EXISTS titles_fts USING fts5(
        key UNINDEXED,
        title_ru,
        title_en,
        title_ja,
        synonyms,
        description_ru,
        tokenize = 'unicode61 remove_diacritics 2'
    );
    """)
    conn.commit()
    conn.close()


def upsert_title(title_obj: dict, db_path: str = DB_PATH) -> int:
    """Inserts or updates a complete title record with all relations and full-text index."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    key = title_obj.get("key")
    if not key:
        raise ValueError("title_obj must contain 'key'")

    sources = title_obj.get("sources", {})
    animan = sources.get("animan", {})
    shk_all = sources.get("shikimori", {})
    shk = shk_all.get("anime", {}) if isinstance(shk_all, dict) else {}
    al = sources.get("anilist", {}) if isinstance(sources.get("anilist"), dict) else {}

    titles_map = animan.get("titles", {})
    def _clean_str(val):
        if isinstance(val, (list, tuple)):
            return " / ".join(str(x) for x in val if x)
        return str(val) if val is not None else None

    main_t = titles_map.get("main", {}) if isinstance(titles_map, dict) else {}
    title_ru = _clean_str(main_t.get("ru") or shk.get("russian") or title_obj.get("names", {}).get("en"))
    title_en = _clean_str(main_t.get("en") or al.get("title", {}).get("english") or title_obj.get("names", {}).get("en"))
    title_ja = _clean_str(main_t.get("ja") or shk.get("japanese") or al.get("title", {}).get("native") or title_obj.get("names", {}).get("jp"))

    all_names = []
    for n in (titles_map.get("all") if isinstance(titles_map, dict) else []) or []:
        if isinstance(n, dict) and n.get("name"):
            val = n.get("name")
            if isinstance(val, (list, tuple)):
                all_names.extend(str(x) for x in val if x)
            elif val:
                all_names.append(str(val))
    synonyms_str = " ".join(all_names)

    shikimori_id = shk.get("id")
    if not shikimori_id and animan.get("franchise"):
        nodes = animan.get("franchise", {}).get("nodes") or []
        if nodes and isinstance(nodes, list) and isinstance(nodes[0], dict):
            shikimori_id = nodes[0].get("id")

    try:
        shikimori_id = int(shikimori_id) if shikimori_id is not None else None
    except (ValueError, TypeError):
        shikimori_id = None

    try:
        anilist_id = int(al.get("id")) if al.get("id") is not None else None
    except (ValueError, TypeError):
        anilist_id = None

    try:
        raw_mal = shk.get("id") or al.get("idMal")
        mal_id = int(raw_mal) if raw_mal is not None else None
    except (ValueError, TypeError):
        mal_id = None

    facts = animan.get("facts", {}) if isinstance(animan, dict) else {}
    fmt = facts.get("format") or (shk.get("kind") or "").upper()
    fmt_ru = facts.get("format_ru")
    status = facts.get("status") or shk.get("status")
    status_ru = facts.get("status_ru")

    year_val = facts.get("year")
    try:
        year = int(str(year_val)[:4]) if year_val else None
    except (ValueError, TypeError):
        year = None

    season = facts.get("season_en") or al.get("season")
    ep_total = facts.get("episodes_total") or al.get("episodes") or shk.get("episodes")
    ep_aired = facts.get("episodes_aired") or shk.get("episodes_aired") or ep_total
    duration_min = facts.get("duration_min") or al.get("duration") or shk.get("duration")

    scores = animan.get("scores", {}) if isinstance(animan, dict) else {}
    score_avg = scores.get("average")
    score_shk = shk.get("score")
    score_al = al.get("averageScore")
    if score_al is not None:
        score_al = round(float(score_al) / 10.0, 2)

    age_rating = facts.get("age_rating") or shk.get("rating")
    age_rating_ru = facts.get("age_rating_ru")

    posters = animan.get("posters") or []
    poster_url = posters[0].get("url") if posters and isinstance(posters[0], dict) else (al.get("coverImage", {}).get("large") if isinstance(al, dict) else None)

    banners = animan.get("banners") or []
    banner_url = banners[0].get("url") if banners and isinstance(banners[0], dict) else (al.get("bannerImage") if isinstance(al, dict) else None)

    desc_obj = animan.get("description", {}) if isinstance(animan, dict) else {}
    desc_ru = desc_obj.get("ru") or shk.get("description") or al.get("description_ru")

    data_json_str = json.dumps(title_obj, ensure_ascii=False)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # 1. Insert/Update titles table
    cur.execute("""
        INSERT INTO titles (
            key, title_ru, title_en, title_ja, shikimori_id, anilist_id, mal_id,
            format, format_ru, status, status_ru, year, season,
            episodes_total, episodes_aired, duration_min,
            score_avg, score_shikimori, score_anilist,
            age_rating, age_rating_ru, poster_url, banner_url,
            description_ru, data_json, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?
        )
        ON CONFLICT(key) DO UPDATE SET
            title_ru = excluded.title_ru,
            title_en = excluded.title_en,
            title_ja = excluded.title_ja,
            shikimori_id = excluded.shikimori_id,
            anilist_id = excluded.anilist_id,
            mal_id = excluded.mal_id,
            format = excluded.format,
            format_ru = excluded.format_ru,
            status = excluded.status,
            status_ru = excluded.status_ru,
            year = excluded.year,
            season = excluded.season,
            episodes_total = excluded.episodes_total,
            episodes_aired = excluded.episodes_aired,
            duration_min = excluded.duration_min,
            score_avg = excluded.score_avg,
            score_shikimori = excluded.score_shikimori,
            score_anilist = excluded.score_anilist,
            age_rating = excluded.age_rating,
            age_rating_ru = excluded.age_rating_ru,
            poster_url = excluded.poster_url,
            banner_url = excluded.banner_url,
            description_ru = excluded.description_ru,
            data_json = excluded.data_json,
            updated_at = excluded.updated_at;
    """, (
        key, title_ru, title_en, title_ja, shikimori_id, anilist_id, mal_id,
        fmt, fmt_ru, status, status_ru, year, season,
        ep_total, ep_aired, duration_min,
        score_avg, score_shk, score_al,
        age_rating, age_rating_ru, poster_url, banner_url,
        desc_ru, data_json_str, now_iso, now_iso
    ))

    cur.execute("SELECT id FROM titles WHERE key = ?", (key,))
    title_id = cur.fetchone()[0]

    # 2. Update Genres
    cur.execute("DELETE FROM title_genres WHERE title_id = ?", (title_id,))
    genres = facts.get("genres") or []
    for g in genres:
        if g:
            cur.execute("INSERT OR IGNORE INTO title_genres (title_id, genre) VALUES (?, ?)", (title_id, g.strip()))

    # 3. Update Animation Studios
    cur.execute("DELETE FROM title_studios WHERE title_id = ?", (title_id,))
    studios = facts.get("studios") or []
    for st in studios:
        if st:
            cur.execute("INSERT OR IGNORE INTO title_studios (title_id, studio) VALUES (?, ?)", (title_id, st.strip()))

    # 4. Update Kodik Voiceover Translations
    cur.execute("DELETE FROM title_translations WHERE title_id = ?", (title_id,))
    kodik = animan.get("kodik") or {}
    for st_name, st_data in kodik.items():
        if isinstance(st_data, dict):
            t_type = st_data.get("type", "voice")
            eps_cnt = st_data.get("episodes_count") or len(st_data.get("episodes", {}))
            cur.execute(
                "INSERT OR IGNORE INTO title_translations (title_id, studio_name, type, episodes_count) VALUES (?, ?, ?, ?)",
                (title_id, st_name.strip(), t_type, eps_cnt)
            )

    # 5. Update FTS5 Virtual Table
    cur.execute("DELETE FROM titles_fts WHERE key = ?", (key,))
    cur.execute(
        "INSERT INTO titles_fts (key, title_ru, title_en, title_ja, synonyms, description_ru) VALUES (?, ?, ?, ?, ?, ?)",
        (key, title_ru or "", title_en or "", title_ja or "", synonyms_str, desc_ru or "")
    )

    conn.commit()
    conn.close()
    return title_id


def query_titles(
    q: str | None = None,
    genres: list[str] | None = None,
    studios: list[str] | None = None,
    voiceovers: list[str] | None = None,
    format: str | None = None,
    status: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    min_score: float | None = None,
    sort: str = "score_desc",
    page: int = 1,
    limit: int = 24,
    db_path: str = DB_PATH,
) -> dict[str, Any]:
    """Rich multi-facet query with filtering, FTS full-text search, and pagination."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    where_clauses = ["1=1"]
    params: list[Any] = []

    # 1. Full-text search
    if q and q.strip():
        clean_q = q.strip().replace('"', '""').replace("'", "''")
        # Support prefix matching for typing
        fts_query = f'"{clean_q}"* OR {clean_q}*'
        where_clauses.append("t.key IN (SELECT key FROM titles_fts WHERE titles_fts MATCH ?)")
        params.append(fts_query)

    # 2. Genre filters (AND logic: must match all specified genres)
    if genres:
        for g in genres:
            if g and g.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_genres WHERE LOWER(genre) = LOWER(?))")
                params.append(g.strip())

    # 3. Animation Studio filter
    if studios:
        for st in studios:
            if st and st.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_studios WHERE LOWER(studio) = LOWER(?))")
                params.append(st.strip())

    # 4. Kodik Voiceover Studio filter
    if voiceovers:
        for vo in voiceovers:
            if vo and vo.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_translations WHERE LOWER(studio_name) LIKE LOWER(?))")
                params.append(f"%{vo.strip()}%")

    # 5. Format filter
    if format and format.strip():
        where_clauses.append("(LOWER(t.format) = LOWER(?) OR LOWER(t.format_ru) = LOWER(?))")
        params.extend([format.strip(), format.strip()])

    # 6. Status filter
    if status and status.strip():
        where_clauses.append("(LOWER(t.status) = LOWER(?) OR LOWER(t.status_ru) = LOWER(?))")
        params.extend([status.strip(), status.strip()])

    # 7. Year range
    if year_from:
        where_clauses.append("t.year >= ?")
        params.append(year_from)
    if year_to:
        where_clauses.append("t.year <= ?")
        params.append(year_to)

    # 8. Minimum score
    if min_score:
        where_clauses.append("t.score_avg >= ?")
        params.append(min_score)

    where_sql = " AND ".join(where_clauses)

    # Sorting
    sort_map = {
        "score_desc": "t.score_avg DESC NULLS LAST, t.year DESC",
        "year_desc": "t.year DESC NULLS LAST, t.score_avg DESC",
        "year_asc": "t.year ASC NULLS LAST, t.score_avg DESC",
        "title_asc": "COALESCE(t.title_ru, t.title_en) ASC",
        "episodes_desc": "t.episodes_total DESC NULLS LAST",
    }
    order_by = sort_map.get(sort, "t.score_avg DESC NULLS LAST")

    # Count total matching records
    count_sql = f"SELECT COUNT(*) FROM titles t WHERE {where_sql}"
    cur.execute(count_sql, params)
    total = cur.fetchone()[0]

    # Pagination
    page = max(1, page)
    limit = max(1, min(100, limit))
    offset = (page - 1) * limit

    query_sql = f"""
        SELECT
            t.id, t.key, t.title_ru, t.title_en, t.title_ja,
            t.format, t.format_ru, t.status, t.status_ru,
            t.year, t.season, t.episodes_total, t.episodes_aired, t.duration_min,
            t.score_avg, t.score_shikimori, t.score_anilist,
            t.age_rating, t.age_rating_ru, t.poster_url, t.banner_url,
            t.description_ru, t.data_json
        FROM titles t
        WHERE {where_sql}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?;
    """
    cur.execute(query_sql, params + [limit, offset])
    rows = cur.fetchall()

    items = []
    for r in rows:
        title_data = json.loads(r["data_json"])
        items.append(title_data)

    conn.close()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        "items": items,
    }


def get_catalog_cards(
    q: str | None = None,
    genres: list[str] | None = None,
    studios: list[str] | None = None,
    voiceovers: list[str] | None = None,
    format: str | None = None,
    status: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    min_score: float | None = None,
    sort: str = "score_desc",
    page: int = 1,
    limit: int = 1000,
    db_path: str = DB_PATH,
) -> dict[str, Any]:
    """Lightning-fast lightweight catalog query (<15ms) for all 1000+ anime titles."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    where_clauses = ["1=1"]
    params: list[Any] = []

    if q and q.strip():
        clean_q = q.strip().replace('"', '""').replace("'", "''")
        fts_query = f'"{clean_q}"* OR {clean_q}*'
        where_clauses.append("t.key IN (SELECT key FROM titles_fts WHERE titles_fts MATCH ?)")
        params.append(fts_query)

    if genres:
        for g in genres:
            if g and g.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_genres WHERE LOWER(genre) = LOWER(?))")
                params.append(g.strip())

    if studios:
        for st in studios:
            if st and st.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_studios WHERE LOWER(studio) = LOWER(?))")
                params.append(st.strip())

    if voiceovers:
        for vo in voiceovers:
            if vo and vo.strip():
                where_clauses.append("t.id IN (SELECT title_id FROM title_translations WHERE LOWER(studio_name) LIKE LOWER(?))")
                params.append(f"%{vo.strip()}%")

    if format and format.strip():
        where_clauses.append("(LOWER(t.format) = LOWER(?) OR LOWER(t.format_ru) = LOWER(?))")
        params.extend([format.strip(), format.strip()])

    if status and status.strip():
        where_clauses.append("(LOWER(t.status) = LOWER(?) OR LOWER(t.status_ru) = LOWER(?))")
        params.extend([status.strip(), status.strip()])

    if year_from:
        where_clauses.append("t.year >= ?")
        params.append(year_from)
    if year_to:
        where_clauses.append("t.year <= ?")
        params.append(year_to)

    if min_score:
        where_clauses.append("t.score_avg >= ?")
        params.append(min_score)

    where_sql = " AND ".join(where_clauses)

    sort_map = {
        "score_desc": "t.score_avg DESC NULLS LAST, t.year DESC",
        "year_desc": "t.year DESC NULLS LAST, t.score_avg DESC",
        "year_asc": "t.year ASC NULLS LAST, t.score_avg DESC",
        "title_asc": "COALESCE(t.title_ru, t.title_en) ASC",
        "episodes_desc": "t.episodes_total DESC NULLS LAST",
    }
    order_by = sort_map.get(sort, "t.score_avg DESC NULLS LAST")

    count_sql = f"SELECT COUNT(*) FROM titles t WHERE {where_sql}"
    cur.execute(count_sql, params)
    total = cur.fetchone()[0]

    page = max(1, page)
    limit = max(1, min(2000, limit))
    offset = (page - 1) * limit

    query_sql = f"""
        SELECT
            t.id, t.key, t.title_ru, t.title_en, t.title_ja,
            t.format, t.format_ru, t.status, t.status_ru,
            t.year, t.episodes_total, t.score_avg,
            t.poster_url, t.banner_url, t.description_ru,
            (SELECT GROUP_CONCAT(genre, '||') FROM title_genres WHERE title_id = t.id) as genres_str,
            (SELECT GROUP_CONCAT(DISTINCT studio_name) FROM title_translations WHERE title_id = t.id) as kodik_studios_str
        FROM titles t
        WHERE {where_sql}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?;
    """
    cur.execute(query_sql, params + [limit, offset])
    rows = cur.fetchall()

    cards = []
    for r in rows:
        genres_list = r["genres_str"].split("||") if r["genres_str"] else []
        studios_list = r["kodik_studios_str"].split(",") if r["kodik_studios_str"] else []
        kodik_obj = {s: {"type": "voice"} for s in studios_list}

        card = {
            "key": r["key"],
            "names": {
                "en": r["title_en"],
                "jp": r["title_ja"],
                "ru": r["title_ru"],
            },
            "sources": {
                "animan": {
                    "titles": {
                        "main": {
                            "ru": r["title_ru"],
                            "en": r["title_en"],
                            "ja": r["title_ja"],
                        }
                    },
                    "facts": {
                        "format_ru": r["format_ru"],
                        "episodes_total": r["episodes_total"],
                        "year": r["year"],
                        "status_ru": r["status_ru"],
                        "genres": genres_list,
                    },
                    "scores": {
                        "average": r["score_avg"],
                    },
                    "posters": [{"url": r["poster_url"]}] if r["poster_url"] else [],
                    "banners": [{"url": r["banner_url"]}] if r["banner_url"] else [],
                    "description": {
                        "ru": r["description_ru"],
                    },
                    "kodik": kodik_obj,
                }
            }
        }
        cards.append(card)

    conn.close()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        "titles": cards,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def get_title_by_key(key: str, db_path: str = DB_PATH) -> dict | None:
    """Fetches a single full anime dossier by its key."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT data_json FROM titles WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row["data_json"])
    return None


def get_all_titles_catalog(db_path: str = DB_PATH, limit: int | None = None) -> dict:
    """Returns the full catalog structured identically to data/anime.json for 100% backward compatibility."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    sql = "SELECT data_json FROM titles ORDER BY score_avg DESC NULLS LAST"
    if limit:
        sql += f" LIMIT {int(limit)}"
    cur.execute(sql)
    
    titles = []
    while True:
        rows = cur.fetchmany(50)
        if not rows:
            break
        for r in rows:
            titles.append(json.loads(r["data_json"]))
    conn.close()

    return {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_count": len(titles),
        "titles": titles,
    }


def get_filter_facets(db_path: str = DB_PATH) -> dict[str, Any]:
    """Returns aggregated metadata facets: genres, studios, translations, formats, years."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Genres with counts
    cur.execute("SELECT genre, COUNT(*) as cnt FROM title_genres GROUP BY genre ORDER BY cnt DESC, genre ASC")
    genres = [{"name": r["genre"], "count": r["cnt"]} for r in cur.fetchall()]

    # Animation Studios with counts
    cur.execute("SELECT studio, COUNT(*) as cnt FROM title_studios GROUP BY studio ORDER BY cnt DESC, studio ASC")
    studios = [{"name": r["studio"], "count": r["cnt"]} for r in cur.fetchall()]

    # Kodik Voiceover Studios with counts
    cur.execute("SELECT studio_name, COUNT(DISTINCT title_id) as cnt FROM title_translations GROUP BY studio_name ORDER BY cnt DESC, studio_name ASC")
    translations = [{"name": r["studio_name"], "count": r["cnt"]} for r in cur.fetchall()]

    # Formats with counts
    cur.execute("SELECT format_ru, COUNT(*) as cnt FROM titles WHERE format_ru IS NOT NULL GROUP BY format_ru ORDER BY cnt DESC")
    formats = [{"name": r["format_ru"], "count": r["cnt"]} for r in cur.fetchall()]

    # Statuses with counts
    cur.execute("SELECT status_ru, COUNT(*) as cnt FROM titles WHERE status_ru IS NOT NULL GROUP BY status_ru ORDER BY cnt DESC")
    statuses = [{"name": r["status_ru"], "count": r["cnt"]} for r in cur.fetchall()]

    # Years range
    cur.execute("SELECT MIN(year) as min_y, MAX(year) as max_y FROM titles WHERE year IS NOT NULL")
    yr = cur.fetchone()
    min_year = yr["min_y"] if yr else 1990
    max_year = yr["max_y"] if yr else 2026

    conn.close()
    return {
        "genres": genres,
        "studios": studios,
        "voiceovers": translations,
        "formats": formats,
        "statuses": statuses,
        "years": {"min": min_year, "max": max_year},
    }
