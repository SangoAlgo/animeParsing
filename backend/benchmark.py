"""Comprehensive Benchmark & Profiler for Anime Parsing Pipeline.

Measures precise parsing / collection duration per title and per source:
- AniList
- Shikimori (parallelized sub-requests)
- AnimeThemes (early exit optimization)
- Manga (parallelized MangaDex, AniList, Shikimori)
- Sakugabooru (Sakuga)
- AniSkip (real frame-accurate timestamps)
- Google Translate (Descriptions + Episode Batch)
- Animan Master Synthesis
- Async Concurrent Pipeline Speedup
"""
from __future__ import annotations

import json
import os
import sys
import time
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from async_collector import collect_single_title_concurrent
from collectors import anilist, animethemes, manga, shikimori
from collectors.animan import build
from collectors.sakuga import fetch_sakuga
from collectors.titles import TITLES
from mappings import mapping_for
from translator import translate_batch, translate_google


def benchmark_single_title_sequential(t: dict) -> dict:
    key = t["key"]
    en_name = t["en"]

    timings = {}
    sources = {}

    # 1. AniList
    t0 = time.perf_counter()
    al_data = anilist.collect(t)
    timings["anilist_sec"] = round(time.perf_counter() - t0, 3)
    sources["anilist"] = al_data

    # 2. Shikimori
    t0 = time.perf_counter()
    shk_data = shikimori.collect(t)
    timings["shikimori_sec"] = round(time.perf_counter() - t0, 3)
    sources["shikimori"] = shk_data

    # 3. AnimeThemes
    t0 = time.perf_counter()
    at_data = animethemes.collect(t)
    timings["animethemes_sec"] = round(time.perf_counter() - t0, 3)
    sources["anime_themes"] = at_data

    # 4. Manga
    t0 = time.perf_counter()
    mn_data = manga.collect(t)
    timings["manga_sec"] = round(time.perf_counter() - t0, 3)
    sources["manga"] = mn_data

    # 5. Sakugabooru
    t0 = time.perf_counter()
    sakuga_data = fetch_sakuga(key, limit=6)
    timings["sakuga_sec"] = round(time.perf_counter() - t0, 3)

    # 6. Google Translate
    t0 = time.perf_counter()
    en_desc = al_data.get("description") or ""
    if en_desc:
        translate_google(en_desc[:300], sl="en", tl="ru")
    timings["google_translate_sec"] = round(time.perf_counter() - t0, 3)

    # 7. Animan Aggregation & AniSkip Timestamps
    t0 = time.perf_counter()
    title_obj = {
        "key": key,
        "names": {"en": en_name, "ja": t.get("jp")},
        "sources": sources,
        "manga_map": mapping_for(key),
    }
    animan_data = build(title_obj, sakuga_clips=sakuga_data)
    timings["animan_sec"] = round(time.perf_counter() - t0, 3)

    total_seq = round(sum(timings.values()), 3)
    timings["total_sequential_sec"] = total_seq

    # 8. Fully Parallel Execution
    t0 = time.perf_counter()
    par_data = collect_single_title_concurrent(t)
    par_time = round(time.perf_counter() - t0, 3)
    timings["parallel_async_sec"] = par_time
    timings["speedup"] = round(total_seq / max(par_time, 0.01), 2)

    return {
        "key": key,
        "name": en_name,
        "timings": timings,
    }


def run_benchmark(sample_size: int = 3) -> dict:
    titles_to_test = TITLES[:sample_size]
    print(f"Profiling {len(titles_to_test)} anime titles in detail...", flush=True)

    results = []
    for i, t in enumerate(titles_to_test, 1):
        print(f"[{i}/{len(titles_to_test)}] Profiling {t['en']}...", flush=True)
        res = benchmark_single_title_sequential(t)
        results.append(res)
        tm = res["timings"]
        print(
            f"   Sequential: {tm['total_sequential_sec']}s (AL:{tm['anilist_sec']}s, Shiki:{tm['shikimori_sec']}s, AT:{tm['animethemes_sec']}s, Manga:{tm['manga_sec']}s, Sakuga:{tm['sakuga_sec']}s, Trans:{tm['google_translate_sec']}s, Animan:{tm['animan_sec']}s)"
        )
        print(f"   Async Parallel: {tm['parallel_async_sec']}s  ->  Speedup: {tm['speedup']}x\n", flush=True)

    return {
        "tested_titles": results,
    }


if __name__ == "__main__":
    report = run_benchmark(sample_size=3)
    with open("data/benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Benchmark complete -> data/benchmark_report.json")
