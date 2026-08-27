"""Fast Enrichment Script for Sakuga and Manga.

Iterates over all 1003 titles in data/anime.db and concurrently enriches them
with dynamic Sakugabooru key animation clips and MangaDex manga chapters/volumes.
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from collectors import manga
from collectors.sakuga import fetch_sakuga
from db import get_connection, DB_PATH
from mappings import mapping_for

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("enrich")


def enrich_single_title(row: dict) -> tuple[str, bool, int, int]:
    key = row["key"]
    data = json.loads(row["data_json"])
    sources = data.get("sources", {})
    animan = sources.get("animan", {})

    en_name = row["title_en"] or data.get("names", {}).get("en") or key

    # 1. Check/Fetch Sakuga
    existing_sakuga = animan.get("sakuga") or []
    if not existing_sakuga:
        sakuga_clips = fetch_sakuga(key, title_name=en_name, limit=6)
    else:
        sakuga_clips = existing_sakuga

    # 2. Check/Fetch Manga
    existing_manga = sources.get("manga") or {}
    has_mangadex = "mangadex" in (existing_manga.get("parts") or {})
    if not has_mangadex:
        entry = {"key": key, "en": en_name}
        manga_data = manga.collect(entry)
    else:
        manga_data = existing_manga

    mn_parts = manga_data.get("parts") or {}
    mn_a = mn_parts.get("anilist") or {}
    mn_s = mn_parts.get("shikimori") or {}
    mn_md = mn_parts.get("mangadex") or {}

    m_sources = {}
    if mn_a:
        cov = mn_a.get("coverImage") or {}
        m_sources["anilist"] = {
            "title": (mn_a.get("title") or {}).get("romaji") or (mn_a.get("title") or {}).get("english"),
            "chapters": mn_a.get("chapters"),
            "volumes": mn_a.get("volumes"),
            "status": mn_a.get("status"),
            "score": mn_a.get("averageScore"),
            "cover": cov.get("extraLarge") or cov.get("large"),
            "url": mn_a.get("siteUrl") or (f"https://anilist.co/manga/{mn_a['id']}" if mn_a.get("id") else None),
        }
    if mn_s:
        m_obj = mn_s.get("manga") or {}
        m_im = m_obj.get("image") or {}
        m_sources["shikimori"] = {
            "title": m_obj.get("name"),
            "title_ru": m_obj.get("russian") or m_obj.get("name"),
            "chapters": m_obj.get("chapters"),
            "volumes": m_obj.get("volumes"),
            "status": m_obj.get("status"),
            "score": m_obj.get("score"),
            "cover": m_im.get("original") or m_im.get("preview"),
            "url": f"https://shikimori.one/mangas/{mn_s['id']}" if mn_s.get("id") else None,
        }
    if mn_md:
        m_sources["mangadex"] = {
            "chapters_en": mn_md.get("chapters_en_total"),
            "last_chapter": (mn_md.get("attributes") or {}).get("lastChapter"),
            "cover": mn_md.get("cover_url"),
            "url": f"https://mangadex.org/title/{mn_md['id']}" if mn_md.get("id") else None,
            "volumes_en": mn_md.get("volumes_en") or [],
        }

    # 3. Build mapping
    ep_cnt = animan.get("facts", {}).get("episodes_total") or data.get("sources", {}).get("anilist", {}).get("episodes") or 12
    m_map = mapping_for(key, manga_part=manga_data, episodes_count=ep_cnt)

    # 4. Inject into animan
    animan["sakuga"] = sakuga_clips
    animan["manga"] = {
        "map": m_map,
        "sources": m_sources,
    }
    sources["manga"] = manga_data
    sources["animan"] = animan
    data["manga_map"] = m_map
    data["sources"] = sources

    # 5. Return updated JSON
    updated_json = json.dumps(data, ensure_ascii=False)
    return key, True, len(sakuga_clips), len(m_map.get("rows", [])), updated_json


def run_enrichment(max_workers: int = 12):
    conn = get_connection(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, key, title_ru, title_en, data_json FROM titles ORDER BY id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    total = len(rows)
    print(f"=== Starting Sakuga & Manga Enrichment for {total} titles ===", flush=True)
    print(f"Workers: {max_workers} threads\n", flush=True)

    t0 = time.perf_counter()
    completed = 0
    total_sakuga_found = 0
    total_manga_found = 0

    # Thread-safe batch updater for SQLite
    write_conn = get_connection(DB_PATH)
    write_cur = write_conn.cursor()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(enrich_single_title, r): r["key"] for r in rows}

        for fut in concurrent.futures.as_completed(futures):
            k = futures[fut]
            try:
                key, success, sakuga_cnt, manga_cnt, updated_json = fut.result()
                if success:
                    write_cur.execute("UPDATE titles SET data_json = ? WHERE key = ?", (updated_json, key))
                    completed += 1
                    if sakuga_cnt > 0:
                        total_sakuga_found += 1
                    if manga_cnt > 0:
                        total_manga_found += 1

                if completed % 25 == 0 or completed == total:
                    write_conn.commit()
                    elapsed = time.perf_counter() - t0
                    speed = completed / elapsed if elapsed > 0 else 0
                    print(
                        f"[{completed:4d}/{total}] ({completed*100/total:5.1f}%) "
                        f"Sakuga: {total_sakuga_found} | Manga: {total_manga_found} | Speed: {speed:.1f} titles/s",
                        flush=True,
                    )
            except Exception as e:
                log.error(f"Error enriching {k}: {e}")

    write_conn.commit()
    write_conn.close()

    total_time = round(time.perf_counter() - t0, 1)
    print(f"\n=== Enrichment Complete in {total_time}s ===", flush=True)
    print(f"Total titles enriched: {completed}/{total}")
    print(f"Titles with Sakuga clips: {total_sakuga_found}")
    print(f"Titles with Manga adaptations: {total_manga_found}")


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    run_enrichment(max_workers=workers)
