"""Directly apply cached filler/canon structures from fillers_cache.json into anime.db."""
import json
import os
import sqlite3
import re

DB_PATH = "data/anime.db"
CACHE_FILE = "data/fillers_cache.json"

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    cache = json.load(f)

print(f"Loaded {len(cache)} shows from {CACHE_FILE}")

# Alias map
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

conn = sqlite3.connect(DB_PATH, timeout=60.0)
conn.execute("PRAGMA journal_mode=WAL;")
c = conn.cursor()
c.execute("SELECT id, key, title_ru, title_en, episodes_total, data_json FROM titles")
rows = c.fetchall()

updates = []
for title_id, key, t_ru, t_en, ep_total, data_raw in rows:
    try:
        d = json.loads(data_raw) if data_raw else {}
    except Exception:
        d = {}

    slug = ALIASES.get(key)
    if not slug and t_en:
        norm = re.sub(r"[^a-z0-9\s]", "", t_en.lower()).replace(" ", "-")
        if norm in cache:
            slug = norm

    filler_dict = cache.get(slug) if slug else None

    # Determine total episode count
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
    updates.append((new_json, len(items), title_id))

c.executemany("UPDATE titles SET data_json = ?, episodes_total = ? WHERE id = ?", updates)
conn.commit()
conn.close()
print(f"✅ Successfully updated {len(updates)} titles in anime.db with filler/canon structures!")
