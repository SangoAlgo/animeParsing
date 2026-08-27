"""Episode Filler & Canon Classification Collector.

Sources:
1. AnimeFillerList (www.animefillerlist.com) - Gold standard for Manga Canon, Filler, Mixed, and Anime Canon
2. Local persistent cache (data/fillers_cache.json)
3. Default Canon Generator for canonical seasonal anime
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("fillers")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fillers_cache.json")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "anime.db")

TYPE_LABELS_RU = {
    "canon": "Манга-канон",
    "anime_canon": "Аниме-канон",
    "mixed": "Смешанный канон",
    "filler": "Филлер",
    "recap": "Рекап (пересказ)",
}


def get_filler_guide(title_key: str, total_eps: int | None = None) -> dict:
    f_map = get_filler_map(title_key, ep_total=total_eps or 12)
    canon_cnt = sum(1 for v in f_map.values() if v.get("filler_type") in ("canon", "anime_canon"))
    filler_cnt = sum(1 for v in f_map.values() if v.get("filler_type") == "filler")
    mixed_cnt = sum(1 for v in f_map.values() if v.get("filler_type") in ("mixed", "recap"))
    return {
        "has_fillers": filler_cnt > 0,
        "canon_count": canon_cnt,
        "filler_count": filler_cnt,
        "mixed_count": mixed_cnt,
        "episodes_map": {k: v.get("filler_type", "canon") for k, v in f_map.items()},
    }


# Manual mapping for top franchises
ALIASES = {
    "naruto": "naruto",
    "naruto-shippuuden": "naruto-shippuden",
    "bleach": "bleach",
    "one-piece": "one-piece",
    "boruto-naruto-next-generations": "boruto-naruto-next-generations",
    "black-clover": "black-clover",
    "fairy-tail": "fairy-tail",
    "fairy-tail-2014": "fairy-tail",
    "dragon-ball": "dragon-ball",
    "dragon-ball-z": "dragon-ball-z",
    "dragon-ball-super": "dragon-ball-super",
    "dragon-ball-gt": "dragon-ball-gt",
    "hunter-x-hunter-2011": "hunter-x-hunter-2011",
    "hunter-x-hunter": "hunter-x-hunter",
    "gintama": "gintama",
    "gintama-2015": "gintama",
    "detective-conan": "detective-conan",
    "meitantei-conan": "detective-conan",
    "boku-no-hero-academia": "my-hero-academia",
    "boku-no-hero-academia-2nd-season": "my-hero-academia",
    "boku-no-hero-academia-3rd-season": "my-hero-academia",
    "boku-no-hero-academia-4th-season": "my-hero-academia",
    "boku-no-hero-academia-5th-season": "my-hero-academia",
    "boku-no-hero-academia-6th-season": "my-hero-academia",
    "shingeki-no-kyojin": "attack-titan",
    "death-note": "death-note",
    "jujutsu-kaisen": "jujutsu-kaisen",
    "jujutsu-kaisen-2nd-season": "jujutsu-kaisen",
    "kimetsu-no-yaiba": "demon-slayer-kimetsu-no-yaiba",
    "kimetsu-no-yaiba-yuukaku-hen": "demon-slayer-kimetsu-no-yaiba",
    "demon-slayer": "demon-slayer-kimetsu-no-yaiba",
    "tokyo-ghoul": "tokyo-ghoul",
    "fullmetal-alchemist": "fullmetal-alchemist",
    "fullmetal-alchemist-brotherhood": "fullmetal-alchemist-brotherhood",
    "fma-brotherhood": "fullmetal-alchemist-brotherhood",
    "rurouni-kenshin": "rurouni-kenshin",
    "inuyasha": "inuyasha",
    "sailor-moon": "sailor-moon",
    "soul-eater": "soul-eater",
    "yu-gi-oh": "yu-gi-oh",
    "pokemon": "pokemon",
    "katekyo-hitman-reborn": "katekyo-hitman-reborn",
    "dgray-man": "d-gray-man",
    "blue-exorcist": "blue-exorcist-ao-no-exorcist",
    "seven-deadly-sins": "seven-deadly-sins",
    "nanatsu-no-taizai": "seven-deadly-sins",
    "cowboy-bebop": "cowboy-bebop",
    "neon-genesis-evangelion": "neon-genesis-evangelion",
    "nge": "neon-genesis-evangelion",
    "code-geass-hangyaku-no-lelouch": "code-geass-lelouch-rebellion",
    "code-geass-hangyaku-no-lelouch-r2": "code-geass-lelouch-rebellion",
    "steins-gate": "steinsgate",
    "toriko": "toriko",
    "beastars": "beastars",
    "mob-psycho-100": "mob-psycho-100",
    "one-punch-man": "one-punch-man",
    "dr-stone": "dr-stone",
    "haikyuu": "haikyu",
    "vinland-saga": "vinland-saga",
    "chainsaw-man": "chainsaw-man",
    "solo-leveling": "solo-leveling",
}


def load_cache() -> dict[str, dict]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: dict[str, dict]):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_show_from_animefillerlist(slug: str) -> dict[str, dict] | None:
    """Scrapes episode list and filler classification from animefillerlist.com."""
    url = f"https://www.animefillerlist.com/shows/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.select_one("table.EpisodeList")
        if not table:
            return None

        episodes = {}
        for tr in table.select("tbody tr"):
            td_num = tr.select_one("td.Number")
            td_title = tr.select_one("td.Title")
            td_type = tr.select_one("td.Type")
            td_date = tr.select_one("td.Date")

            if td_num and td_type:
                try:
                    num = int(td_num.text.strip())
                except Exception:
                    continue
                type_raw = td_type.text.strip().lower()
                title_text = td_title.text.strip() if td_title else f"Серия {num}"

                if "manga canon" in type_raw:
                    f_type = "canon"
                    f_label = "Канон манги"
                elif "anime canon" in type_raw:
                    f_type = "anime_canon"
                    f_label = "Аниме-канон"
                elif "mixed" in type_raw:
                    f_type = "mixed"
                    f_label = "Смешанный канон"
                elif "filler" in type_raw:
                    f_type = "filler"
                    f_label = "Филлер"
                else:
                    f_type = "canon"
                    f_label = "Канон"

                episodes[str(num)] = {
                    "number": num,
                    "title": f"Серия {num}",
                    "title_en": title_text,
                    "filler_type": f_type,
                    "filler_label": f_label,
                    "air_date": td_date.text.strip() if td_date else None,
                }
        return episodes
    except Exception as e:
        log.warning("Failed to fetch filler info for %s: %s", slug, e)
        return None


def get_filler_map(key: str, title_en: str = "", ep_total: int = 12) -> dict[str, dict]:
    """Returns episode filler mapping for a title."""
    cache = load_cache()
    slug = ALIASES.get(key) or ALIASES.get(key.lower())
    if not slug and title_en:
        norm = re.sub(r"[^a-z0-9\s]", "", title_en.lower()).replace(" ", "-")
        slug = norm

    if slug and slug in cache:
        return cache[slug]

    if slug:
        fetched = fetch_show_from_animefillerlist(slug)
        if fetched:
            cache[slug] = fetched
            save_cache(cache)
            return fetched

    # Generate standard Canon structure for titles without fillers
    episodes = {}
    count = ep_total or 12
    for n in range(1, count + 1):
        episodes[str(n)] = {
            "number": n,
            "title": f"Серия {n}",
            "title_en": f"Episode {n}",
            "filler_type": "canon",
            "filler_label": "Канон манги",
            "air_date": None,
        }
    return episodes


def enrich_database_fillers():
    """Scrapes, caches and injects authentic filler/canon structures into all titles in anime.db."""
    log.info("Starting Episode Fillers & Canon DB Enrichment...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, key, title_ru, title_en, episodes_total, data_json FROM titles")
    rows = c.fetchall()
    log.info("Loaded %d titles from DB", len(rows))

    # Pre-fetch all known slug matches in parallel
    unique_slugs = set(ALIASES.values())
    cache = load_cache()
    to_fetch = [s for s in unique_slugs if s not in cache]
    log.info("Need to fetch %d unique filler shows from AnimeFillerList...", len(to_fetch))

    if to_fetch:
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_slug = {executor.submit(fetch_show_from_animefillerlist, s): s for s in to_fetch}
            for future in as_completed(future_to_slug):
                s = future_to_slug[future]
                try:
                    res = future.result()
                    if res:
                        cache[s] = res
                        log.info("✓ Fetched %d episodes for '%s'", len(res), s)
                except Exception as e:
                    log.warning("Error fetching %s: %s", s, e)
        save_cache(cache)

    # Now update SQLite data_json for all 1,003 titles
    updated_count = 0
    for title_id, key, t_ru, t_en, ep_total, data_raw in rows:
        try:
            d = json.loads(data_raw) if data_raw else {}
        except Exception:
            d = {}

        slug = ALIASES.get(key)
        filler_dict = None
        if slug and slug in cache:
            filler_dict = cache[slug]

        total_ep_count = ep_total or (len(filler_dict) if filler_dict else 12)
        if filler_dict:
            total_ep_count = max(total_ep_count, len(filler_dict))

        items = []
        canon_count = 0
        filler_count = 0
        mixed_count = 0
        anime_canon_count = 0

        for n in range(1, total_ep_count + 1):
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

            if f_type == "canon":
                canon_count += 1
            elif f_type == "filler":
                filler_count += 1
            elif f_type == "mixed":
                mixed_count += 1
            elif f_type == "anime_canon":
                anime_canon_count += 1

            items.append({
                "number": n,
                "title": f"Серия {n}",
                "title_en": t_en_ep,
                "filler_type": f_type,
                "filler_label": f_label,
            })

        d["episodes"] = {
            "count": len(items),
            "canon_count": canon_count,
            "filler_count": filler_count,
            "mixed_count": mixed_count,
            "anime_canon_count": anime_canon_count,
            "items": items,
        }

        new_json = json.dumps(d, ensure_ascii=False)
        c.execute("UPDATE titles SET data_json = ?, episodes_total = ? WHERE id = ?", (new_json, len(items), title_id))
        updated_count += 1

    conn.commit()
    conn.close()
    log.info("✅ Finished! Successfully enriched %d titles with authentic Canon/Filler structures.", updated_count)


if __name__ == "__main__":
    enrich_database_fillers()
