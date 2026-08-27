"""AnimeThemes.moe API collector (theme songs database, public)."""
from __future__ import annotations

import urllib.parse

from .web import http_get_json

BASE = "https://api.animethemes.moe"


def _resolve_id(entry: dict) -> tuple[int, str] | None:
    """Search several name variants; score matches: exact name/slug beats substring."""
    best = None
    best_score = 0
    queries = dict.fromkeys([entry["en"], entry.get("jp", ""), *entry.get("aliases", [])])
    for q in queries:
        if not q:
            continue
        try:
            resp = http_get_json(
                f"{BASE}/search?q={urllib.parse.quote(q)}", retries=3, timeout=12,
                use_insecure_ssl=False,
            )
            for item in resp.get("search", {}).get("anime", []) or []:
                slug = (item.get("slug") or "").lower()
                name = (item.get("name") or "").lower()
                want = q.lower().strip()
                if not want:
                    continue
                score = 0
                if name == want or slug == want:
                    score = 3
                elif slug == want.replace(" ", "_"):
                    score = 3
                elif (name.startswith(want) or slug.startswith(want.replace(" ", "_"))):
                    score = 2
                elif want in name or want in slug.replace("_", " "):
                    score = 1
                if score > best_score:
                    best_score = score
                    best = (item["id"], slug)
                    if best_score == 3:
                        return best
        except Exception:
            pass
        if best_score == 3:
            return best
    return best


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"AnimeThemes for {entry['en']}")
    resolved = _resolve_id(entry)
    result = {"source": "anime_themes", "id": None, "slug": None, "anime": None}
    if resolved is None:
        result["error"] = "not found"
        return result
    aid, slug = resolved
    result["id"] = aid
    result["slug"] = slug
    inc = "animethemes.animethemeentries.videos.audio,animethemes.song.artists"
    data = http_get_json(
        f"{BASE}/anime/{slug}?include={inc}", retries=4, use_insecure_ssl=False,
    )
    anime = data.get("anime")
    if isinstance(anime, list):
        anime = anime[0] if anime else None
    result["anime"] = anime
    return result