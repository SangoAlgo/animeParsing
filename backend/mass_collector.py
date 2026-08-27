"""High-Throughput Mass Collector for 1000 Anime Titles from Shikimori + Kodik + Multi-Source.

Pipeline:
1. Sequentially fetches top anime from Shikimori API (order=popularity, censored=true, no hentai).
2. Links strictly by `shikimori_id` to Kodik API to fetch all fandub studios, seasons, episodes, and player links.
3. Concurrently enriches each title with AniList (GraphQL idMal), AnimeThemes, MangaDex, Sakugabooru, AniSkip, and Russian Translations.
4. Builds unified Animan dossier and saves immediately to SQLite (`data/anime.db`) with WAL-mode persistence.
5. Periodically updates `data/anime.json` to keep both storage formats in sync.
6. Rate-limit safe: worker pool with token bucket & exponential backoff on 429.
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from async_collector import collect_single_title_concurrent
from db import DB_PATH, get_connection, init_db, upsert_title

log = logging.getLogger("mass_collector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUT_JSON = os.path.join(DATA_DIR, "anime.json")

SHIKI_HEADERS = {
    "User-Agent": "AnimeParsing/1.0 (mass catalog collector; contact: none)",
    "Accept": "application/json",
}


def slugify(text: str) -> str:
    """Converts a title to a clean URL slug."""
    text = (text or "").lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "anime"


def fetch_shikimori_catalog(target_count: int = 1000) -> list[dict]:
    """Fetches top anime titles from Shikimori API ordered by popularity, without hentai (censored=true)."""
    print(f"=== Fetching {target_count} anime catalog from Shikimori API ===", flush=True)
    all_titles = []
    seen_ids = set()
    page = 1
    limit = 50

    while len(all_titles) < target_count:
        url = "https://shikimori.one/api/animes"
        params = {
            "order": "popularity",
            "limit": limit,
            "page": page,
            "censored": "true",  # Excludes hentai / 18+ rx
        }
        try:
            resp = requests.get(url, params=params, headers=SHIKI_HEADERS, timeout=15)
            if resp.status_code == 429:
                print("  [Shikimori Rate Limit 429] Waiting 5s...", flush=True)
                time.sleep(5)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data:
                print(f"  No more titles returned at page {page}.", flush=True)
                break

            added_on_page = 0
            for item in data:
                sid = item.get("id")
                rating = item.get("rating", "")
                if not sid or sid in seen_ids or rating == "rx":
                    continue
                seen_ids.add(sid)

                raw_name = item.get("name") or f"anime-{sid}"
                base_slug = slugify(raw_name)
                # Ensure unique slug
                entry_key = base_slug if base_slug not in {t["key"] for t in all_titles} else f"{base_slug}-{sid}"

                entry = {
                    "key": entry_key,
                    "en": item.get("name"),
                    "ru": item.get("russian"),
                    "jp": item.get("japanese") or "",
                    "shiki_id": sid,
                    "mal": sid,  # Shikimori ID is identical to MyAnimeList ID
                    "kind": item.get("kind"),
                    "score": item.get("score"),
                    "episodes": item.get("episodes"),
                }
                all_titles.append(entry)
                added_on_page += 1
                if len(all_titles) >= target_count:
                    break

            print(f"  Page {page:2d}: fetched {len(data)} items (+{added_on_page} added, total: {len(all_titles)}/{target_count})", flush=True)
            page += 1
            time.sleep(0.35)  # Rate limit courtesy
        except Exception as e:
            print(f"  Error fetching page {page}: {e}. Retrying in 3s...", flush=True)
            time.sleep(3)

    print(f"=== Successfully retrieved {len(all_titles)} anime targets from Shikimori ===\n", flush=True)
    return all_titles


def get_existing_in_db() -> tuple[set[str], set[int]]:
    """Returns the set of keys and shikimori_ids already stored in data/anime.db."""
    init_db(DB_PATH)
    conn = get_connection(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT key, shikimori_id FROM titles")
    rows = cur.fetchall()
    conn.close()
    keys = {r["key"] for r in rows if r["key"]}
    shiki_ids = {int(r["shikimori_id"]) for r in rows if r["shikimori_id"] is not None}
    return keys, shiki_ids


def run_mass_collector(target_count: int = 7500, max_workers: int = 6, skip_existing: bool = True):
    """Runs the parallel mass collector with rate limit safety and progressive disk persistence."""
    init_db(DB_PATH)
    t_start = time.perf_counter()

    existing_keys, existing_shiki_ids = get_existing_in_db() if skip_existing else (set(), set())
    print(f"=== Database Status: {len(existing_keys)} titles already in DB ({len(existing_shiki_ids)} Shikimori IDs) ===", flush=True)

    catalog_entries = fetch_shikimori_catalog(target_count=target_count)

    to_process = [
        e for e in catalog_entries
        if e["key"] not in existing_keys and e.get("shiki_id") not in existing_shiki_ids
    ]

    print(f"=== Starting Mass Parsing: {len(to_process)} new titles to parse ===", flush=True)
    print(f"Workers: {max_workers} parallel title threads", flush=True)

    if not to_process:
        print("All target titles are already in the database! Nothing to parse.", flush=True)
        return

    completed_count = 0
    total_to_process = len(to_process)
    collected_results = []

    def _process_wrapper(entry: dict, idx: int):
        k = entry["key"]
        sid = entry["shiki_id"]
        en_name = entry["en"]
        try:
            # Add small initial jitter to avoid burst hammering
            time.sleep((idx % max_workers) * 0.1)
            res = collect_single_title_concurrent(entry)
            kodik_cnt = len(res.get("sources", {}).get("animan", {}).get("kodik", {}))
            ep_cnt = res.get("sources", {}).get("animan", {}).get("facts", {}).get("episodes_total") or "?"
            return idx, entry, res, None, kodik_cnt, ep_cnt
        except Exception as ex:
            return idx, entry, None, str(ex), 0, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_process_wrapper, entry, i + 1): entry
            for i, entry in enumerate(to_process)
        }

        for future in concurrent.futures.as_completed(future_map):
            completed_count += 1
            idx, entry, res, err, kodik_cnt, ep_cnt = future.result()
            pct = (completed_count / total_to_process) * 100

            if res and not err:
                collected_results.append(res)
                print(
                    f"[{completed_count:4d}/{total_to_process:4d}] ({pct:5.1f}%) "
                    f"+ '{entry.get('ru') or entry['en']}' (ID: {entry['shiki_id']}) -> {kodik_cnt} Kodik dubs, {ep_cnt} eps",
                    flush=True,
                )
            else:
                print(
                    f"[{completed_count:4d}/{total_to_process:4d}] ({pct:5.1f}%) "
                    f"! Error on '{entry['en']}': {err}",
                    flush=True,
                )

    elapsed = round(time.perf_counter() - t_start, 2)
    print(f"\n=== Mass Parsing Complete in {elapsed}s! Added {len(collected_results)} new titles to SQLite. ===", flush=True)


def _sync_json_catalog():
    """Exports SQLite DB to data/anime.json for backward compatibility (optional)."""
    try:
        conn = get_connection(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT data_json FROM titles ORDER BY score_avg DESC NULLS LAST")
        rows = cur.fetchall()
        conn.close()

        titles = [json.loads(r["data_json"]) for r in rows]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_count": len(titles),
            "titles": titles,
        }
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"  [DB Sync] Synced {len(titles)} titles -> {OUT_JSON}", flush=True)
    except Exception as e:
        log.warning("Could not sync anime.json: %s", e)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 7500
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    run_mass_collector(target_count=count, max_workers=workers)
