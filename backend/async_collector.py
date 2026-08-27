"""Asynchronous Multi-Source Collector with Maximum Parallelism.

Features:
- Intra-title concurrency: 8 concurrent workers per title (AniList, Shikimori, AnimeThemes, MangaDex, Sakuga, AniSkip, FAQ, Google Translate).
- Early translation pipeline: Google Translate runs in parallel the instant AniList finishes.
- Inter-title concurrency: Thread pool for catalog-level batch scraping.
- Automatic retry on transient network errors.
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aniskip import get_title_skips
from collectors import anilist, animethemes, manga, shikimori
from collectors.animan import build as build_animan
from collectors.sakuga import fetch_sakuga
from collectors.titles import TITLES
from db import upsert_title
from faq import get_anime_faq
from mappings import mapping_for
from translator import translate_batch, translate_google

log = logging.getLogger("async_collector")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUT_PATH = os.path.join(DATA_DIR, "anime.json")


def _translate_anilist_payload(al_data: dict) -> dict:
    """Extracts description and episode titles from AniList and translates in parallel."""
    out = {
        "description_ru": None,
        "translated_episodes": [],
    }
    if not al_data:
        return out

    # 1. Translate description
    raw_desc = al_data.get("description") or ""
    if raw_desc:
        clean_desc = re.sub(r"<[^>]+>", "", raw_desc).strip()
        if clean_desc:
            out["description_ru"] = translate_google(clean_desc, sl="en", tl="ru")

    # 2. Translate episode titles in batch
    episodes = al_data.get("streamingEpisodes") or []
    if episodes:
        clean_titles = []
        for i, ep in enumerate(episodes, 1):
            raw_title = ep.get("title") or f"Episode {i}"
            m = re.match(r"(?:Episode|Ep\.?)\s*(\d+)(?:\s*[-–:]\s*(.*))?", raw_title, re.IGNORECASE)
            clean_titles.append(m.group(2).strip() if m and m.group(2) else raw_title)

        out["translated_episodes"] = translate_batch(clean_titles, sl="en", tl="ru")

    return out


def _fetch_with_retry(fn, *args, retries=1, **kwargs):
    """Executes a function with an optional retry."""
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(0.5)


def collect_single_title_concurrent(entry: dict, progress=None) -> dict:
    """Collects all 4 sources, sakuga, FAQ, aniskip, episode streams, and translations concurrently."""
    key = entry["key"]
    en_name = entry["en"]
    ru_name_entry = entry.get("ru") or en_name
    t_start = time.perf_counter()

    if progress:
        progress(f"Starting concurrent collection for {en_name} ({key})...")

    sources = {}
    errors = {}
    timings = {}
    mal_id = entry.get("mal") or entry.get("shiki_id")

    EPS_COUNT_MAP = {
        'cowboy-bebop': 26,
        'death-note': 37,
        'fma-brotherhood': 64,
        'steins-gate': 24,
        'attack-on-titan': 25,
        'nge': 26,
        'spirited-away': 1,
        'your-name': 1,
        'one-punch-man': 12,
        'demon-slayer': 26,
    }
    RU_NAMES_MAP = {
        'cowboy-bebop': 'Ковбой Бибоп',
        'death-note': 'Тетрадь смерти',
        'fma-brotherhood': 'Стальной алхимик: Братство',
        'steins-gate': 'Врата Штейна',
        'attack-on-titan': 'Атака титанов',
        'nge': 'Евангелион нового поколения',
        'spirited-away': 'Унесённые призраками',
        'your-name': 'Твоё имя',
        'one-punch-man': 'Ванпанчмен',
        'demon-slayer': 'Истребитель демонов',
    }
    YEAR_MAP = {
        'cowboy-bebop': 1998,
        'death-note': 2006,
        'fma-brotherhood': 2009,
        'steins-gate': 2011,
        'attack-on-titan': 2013,
        'nge': 1995,
        'spirited-away': 2001,
        'your-name': 2016,
        'one-punch-man': 2015,
        'demon-slayer': 2019,
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # Start all source fetchers, aniskip, and faq in parallel
        f_al = executor.submit(_fetch_with_retry, anilist.collect, entry)
        f_shk = executor.submit(_fetch_with_retry, shikimori.collect, entry)
        f_at = executor.submit(_fetch_with_retry, animethemes.collect, entry)
        f_manga = executor.submit(_fetch_with_retry, manga.collect, entry)
        f_sakuga = executor.submit(fetch_sakuga, key, en_name, 6)
        f_faq = executor.submit(get_anime_faq, key)
        f_aniskip = executor.submit(get_title_skips, mal_id, 30) if mal_id else None

        # Wait for AniList first to start translation early
        try:
            al_data = f_al.result()
            sources["anilist"] = al_data
            timings["anilist_s"] = round(time.perf_counter() - t_start, 3)

            # Instantly launch translation in background while other sources are still downloading!
            f_trans = executor.submit(_translate_anilist_payload, al_data)
        except Exception as e:
            errors["anilist"] = {"type": type(e).__name__, "message": str(e)}
            f_trans = None

        # Collect remaining sources as they resolve
        try:
            sources["shikimori"] = f_shk.result()
        except Exception as e:
            errors["shikimori"] = {"type": type(e).__name__, "message": str(e)}

        try:
            sources["anime_themes"] = f_at.result()
        except Exception as e:
            errors["anime_themes"] = {"type": type(e).__name__, "message": str(e)}

        try:
            sources["manga"] = f_manga.result()
        except Exception as e:
            errors["manga"] = {"type": type(e).__name__, "message": str(e)}

        try:
            sakuga_clips = f_sakuga.result()
        except Exception as e:
            sakuga_clips = []
            errors["sakuga"] = {"type": type(e).__name__, "message": str(e)}

        # Await AniSkip prefetch
        if f_aniskip:
            try:
                f_aniskip.result()
            except Exception:
                pass

        # Await translation results
        try:
            translated_info = f_trans.result() if f_trans else {}
            if translated_info and "anilist" in sources and sources["anilist"]:
                sources["anilist"]["description_ru"] = translated_info.get("description_ru")
                sources["anilist"]["translated_episodes"] = translated_info.get("translated_episodes")
        except Exception as e:
            translated_info = {}

    # Generate complete Manga mapping with MangaDex volumes & chapters
    manga_part = sources.get("manga")
    shk_eps = sources.get("shikimori", {}).get("anime", {}).get("episodes") if isinstance(sources.get("shikimori"), dict) else None
    al_eps = sources.get("anilist", {}).get("episodes") if isinstance(sources.get("anilist"), dict) else None
    ep_total = entry.get("episodes") or shk_eps or al_eps or 12

    m_map = mapping_for(key, manga_part=manga_part, episodes_count=ep_total)

    # Generate complete Fillers & Canon classification from AnimeFillerList
    from collectors.fillers import get_filler_map
    filler_dict = get_filler_map(key, en_name, ep_total)
    ep_count = max(ep_total or 12, len(filler_dict) if filler_dict else 0)

    translated_eps = translated_info.get("translated_episodes") or []
    ep_items = []
    canon_count = 0
    filler_count = 0
    mixed_count = 0
    anime_canon_count = 0

    for n in range(1, ep_count + 1):
        s_n = str(n)
        if filler_dict and s_n in filler_dict:
            info = filler_dict[s_n]
            f_type = info["filler_type"]
            f_label = info["filler_label"]
            t_en_ep = info.get("title_en") or f"Episode {n}"
        else:
            f_type = "canon"
            f_label = "Канон манги"
            t_en_ep = f"Episode {n}"

        t_ru_ep = translated_eps[n - 1] if n - 1 < len(translated_eps) else None

        if f_type == "canon":
            canon_count += 1
        elif f_type == "filler":
            filler_count += 1
        elif f_type == "mixed":
            mixed_count += 1
        elif f_type == "anime_canon":
            anime_canon_count += 1

        ep_items.append({
            "number": n,
            "title": f"Серия {n}",
            "title_ru": t_ru_ep,
            "title_en": t_en_ep,
            "filler_type": f_type,
            "filler_label": f_label,
        })

    episodes_obj = {
        "count": len(ep_items),
        "canon_count": canon_count,
        "filler_count": filler_count,
        "mixed_count": mixed_count,
        "anime_canon_count": anime_canon_count,
        "items": ep_items,
    }

    # Build unified Animan payload
    title_obj = {
        "key": key,
        "names": {"en": en_name, "jp": entry.get("jp")},
        "sources": sources,
        "manga_map": m_map,
        "episodes": episodes_obj,
    }

    try:
        animan_payload = build_animan(title_obj, sakuga_clips=sakuga_clips)
        animan_payload["episodes"] = episodes_obj
        sources["animan"] = animan_payload
    except Exception as e:
        errors["animan"] = {"type": type(e).__name__, "message": str(e)}

    total_duration = round(time.perf_counter() - t_start, 3)

    if progress:
        err_cnt = len(errors)
        progress(f"Finished {en_name} in {total_duration}s ({err_cnt} errors)")

    out_title = {
        "key": key,
        "names": {"en": en_name, "jp": entry.get("jp")},
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": total_duration,
        "sources": sources,
        "errors": errors,
        "manga_map": m_map,
        "episodes": episodes_obj,
    }

    try:
        upsert_title(out_title)
    except Exception as e:
        log.warning("Failed to upsert %s into SQLite: %s", key, e)

    return out_title


def collect_all_concurrent(titles: list[dict] | None = None, max_title_workers: int = 3) -> dict:
    """Collects all titles concurrently using a pool of workers."""
    all_titles = titles or TITLES
    print(f"=== Ultra-Fast Concurrent Collector: {len(all_titles)} titles ===", flush=True)

    t_catalog_start = time.perf_counter()
    results = [None] * len(all_titles)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_title_workers) as executor:
        future_to_idx = {
            executor.submit(collect_single_title_concurrent, t, progress=lambda msg, k=t['key']: print(f"[{k}] {msg}", flush=True)): i
            for i, t in enumerate(all_titles)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                t_def = all_titles[idx]
                results[idx] = {
                    "key": t_def["key"],
                    "names": {"en": t_def["en"], "jp": t_def.get("jp")},
                    "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                    "sources": {},
                    "errors": {"global": str(e)},
                }

    total_duration = round(time.perf_counter() - t_catalog_start, 2)

    db = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_duration_s": total_duration,
        "titles": results,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    ok_count = sum(len(t.get("sources", {})) for t in results)
    err_count = sum(len(t.get("errors", {})) for t in results)

    print(
        f"\n=== Finished in {total_duration}s: {len(results)} titles, "
        f"{ok_count} source payloads, {err_count} errors. Saved -> {OUT_PATH} ===",
        flush=True,
    )
    return db


if __name__ == "__main__":
    collect_all_concurrent()
