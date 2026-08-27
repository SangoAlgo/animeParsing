"""Fast Concurrent Orchestrator: collects all titles from the core sources into data/anime.json.

Uses backend/async_collector.py for maximum parallelism across all sub-processes:
- AniList, Shikimori (7 endpoints), AnimeThemes, Manga (3 sources), Sakuga, AniSkip, FAQ, Google Translate.

Usage:
  python collect.py              # Full concurrent catalog scraping
  python collect.py cowboy-bebop # Single title scraping
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from async_collector import collect_all_concurrent, collect_single_title_concurrent
from collectors.titles import TITLES


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        wanted_keys = set(args)
        titles = [t for t in TITLES if t["key"] in wanted_keys]
        if not titles:
            print(f"No matching titles found for: {args}")
            return
        collect_all_concurrent(titles, max_title_workers=len(titles))
    else:
        collect_all_concurrent(TITLES, max_title_workers=3)


if __name__ == "__main__":
    main()