"""Anime Filler & Canon Guide.

Provides canon/filler classification for anime episodes:
- manga_canon: 100% faithful to the manga storyline (🟢)
- anime_canon: canonical to the anime story, supervised by author (🟡)
- mixed: mixed canon and filler content (🟠)
- filler: non-canon anime-original content / fillers (🔴)
- recap: summary / recap episodes (⚪)
"""
from __future__ import annotations

import re
import urllib.request
import json
import logging

log = logging.getLogger("fillers")

# Curated filler classifications for the active catalog
CURATED_FILLERS = {
    "cowboy-bebop": {
        "canon_type": "original",
        "filler_percent": 0,
        "note": "Оригинальный сериал Studio Sunrise: все 26 серий являются каноническим сюжетом.",
        "episodes": {i: "canon" for i in range(1, 27)},
    },
    "death-note": {
        "canon_type": "manga_canon",
        "filler_percent": 0,
        "note": "Почти 100% экранизация манги. Эпизод 26 является рекапом противостояния Лайта и L.",
        "episodes": {
            **{i: "canon" for i in range(1, 26)},
            26: "recap",
            **{i: "canon" for i in range(27, 38)},
        },
    },
    "fma-brotherhood": {
        "canon_type": "manga_canon",
        "filler_percent": 0,
        "note": "Экранизация манги. Эпизод 1 содержит аниме-оригинальное введение Айзека Макдугала (аниме-канон), серии 2–64 точно следуют манге.",
        "episodes": {
            1: "anime_canon",
            **{i: "canon" for i in range(2, 65)},
        },
    },
    "attack-on-titan": {
        "canon_type": "manga_canon",
        "filler_percent": 0,
        "note": "Полная экранизация манги Хадзимэ Исаямы без филлеров. Серии 1–94 являются строгим каноном (эпизод 13.5 — рекап).",
        "episodes": {i: "canon" for i in range(1, 95)},
    },
    "steins-gate": {
        "canon_type": "novel_canon",
        "filler_percent": 0,
        "note": "Экранизация визуальной новеллы 5pb. Серии 1–24 покрывают истинную концовку (канон). Эпизод 25 — спешл «Эгоистичный дежавю».",
        "episodes": {**{i: "canon" for i in range(1, 25)}, 25: "anime_canon"},
    },
    "nge": {
        "canon_type": "original",
        "filler_percent": 0,
        "note": "Оригинальный сериал Gainax/Анно. Все 26 серий — канон (эпизод 14 содержит рекап первой половины).",
        "episodes": {**{i: "canon" for i in range(1, 14)}, 14: "recap", **{i: "canon" for i in range(15, 27)}},
    },
    "spirited-away": {
        "canon_type": "film_canon",
        "filler_percent": 0,
        "note": "Полнометражный фильм Хаяо Миядзаки (100% авторский канон).",
        "episodes": {1: "canon"},
    },
    "one-punch-man": {
        "canon_type": "manga_canon",
        "filler_percent": 0,
        "note": "Сезоны 1 и 2 экранизируют мангу ONE / Мураты (серии 1–24 — канон).",
        "episodes": {i: "canon" for i in range(1, 25)},
    },
    "your-name": {
        "canon_type": "film_canon",
        "filler_percent": 0,
        "note": "Полнометражный фильм Макото Синкая (100% авторский канон).",
        "episodes": {1: "canon"},
    },
    "demon-slayer": {
        "canon_type": "manga_canon",
        "filler_percent": 0,
        "note": "Последовательная экранизация манги студией Ufotable. Серия 1 арки «Поезд Мугэн» — аниме-оригинальный канон о Рэнгоку, остальные серии — манга-канон.",
        "episodes": {
            **{i: "canon" for i in range(1, 27)},
            27: "anime_canon",
            **{i: "canon" for i in range(28, 66)},
        },
    },
}

TYPE_LABELS_RU = {
    "canon": "Манга-канон",
    "anime_canon": "Аниме-канон",
    "mixed": "Смешанный канон",
    "filler": "Филлер",
    "recap": "Рекап (пересказ)",
}


def get_filler_guide(title_key: str, total_eps: int | None = None) -> dict:
    cur = CURATED_FILLERS.get(title_key)
    if cur:
        eps_map = cur.get("episodes", {})
        canon_cnt = sum(1 for v in eps_map.values() if v in ("canon", "anime_canon"))
        filler_cnt = sum(1 for v in eps_map.values() if v == "filler")
        recap_cnt = sum(1 for v in eps_map.values() if v == "recap")
        mixed_cnt = sum(1 for v in eps_map.values() if v == "mixed")

        return {
            "has_fillers": filler_cnt > 0,
            "filler_percent": cur.get("filler_percent", 0),
            "note": cur.get("note"),
            "canon_count": canon_cnt,
            "filler_count": filler_cnt,
            "recap_count": recap_cnt,
            "mixed_count": mixed_cnt,
            "episodes_map": {str(k): v for k, v in eps_map.items()},
        }

    # Default fallback
    n = total_eps or 1
    return {
        "has_fillers": False,
        "filler_percent": 0,
        "note": "Все вышедшие серии являются каноническими.",
        "canon_count": n,
        "filler_count": 0,
        "recap_count": 0,
        "mixed_count": 0,
        "episodes_map": {str(i): "canon" for i in range(1, n + 1)},
    }
