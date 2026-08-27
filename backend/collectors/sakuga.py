"""Sakugabooru Collector with dynamic tag discovery and animator attribution.

Fetches key animation (sakuga) clips, animator credits, and notable action sequences
from the public Sakugabooru API for any anime title dynamically.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request

log = logging.getLogger("sakuga")

SAKUGA_TAGS = {
    "cowboy-bebop": "cowboy_bebop",
    "death-note": "death_note",
    "fma-brotherhood": "fullmetal_alchemist_brotherhood",
    "attack-on-titan": "shingeki_no_kyojin",
    "steins-gate": "steins;gate",
    "nge": "neon_genesis_evangelion",
    "spirited-away": "spirited_away",
    "one-punch-man": "one-punch_man",
    "your-name": "kimi_no_na_wa",
    "demon-slayer": "kimetsu_no_yaiba",
}

NON_ANIMATOR_TAGS = {
    "animated", "effects", "fighting", "smears", "debris", "explosions",
    "impact_frames", "smoke", "fire", "lightning", "liquid", "beams",
    "running", "hair", "character_acting", "fabric", "gun", "cgi",
    "rotoscope", "creatures", "morphing", "camera_movement", "sparks",
    "presumed", "unconfirmed", "production_materials", "genga", "douga",
    "layout", "storyboard", "corrected",
}


def _clean_slug(text: str) -> str:
    text = re.sub(r"\s*\(?(19\d\d|20\d\d)\)?", "", text or "")
    text = re.sub(r"\s*\(?(season|part|tv)\s*\d*\)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s-]", "", text).lower()
    return re.sub(r"[\s-]+", "_", text).strip("_")


def _find_sakugabooru_tag(candidate_name: str) -> str | None:
    """Finds the official copyright tag on Sakugabooru via tag search API."""
    slug = _clean_slug(candidate_name)
    if not slug:
        return None

    words = slug.split("_")
    search_terms = [slug]
    if len(words) >= 2:
        search_terms.append(f"{words[0]}_{words[1]}")
    search_terms.append(words[0])

    for term in search_terms:
        if len(term) < 3:
            continue
        url = f"https://www.sakugabooru.com/tag.json?name={urllib.parse.quote(term)}&type=3"
        req = urllib.request.Request(url, headers={"User-Agent": "AnimeParsing/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                tags = json.load(resp)
            if tags and isinstance(tags, list):
                tags.sort(key=lambda t: t.get("count", 0), reverse=True)
                # Pick the best tag with highest posts count
                for t_obj in tags:
                    t_name = t_obj.get("name")
                    if t_name and t_obj.get("count", 0) > 0:
                        return t_name
        except Exception:
            continue
    return None


def fetch_sakuga(title_key: str, title_name: str | None = None, limit: int = 6) -> list[dict]:
    """Dynamically fetches top sakuga clips for any anime title."""
    tag = SAKUGA_TAGS.get(title_key)
    if not tag:
        # 1. Try direct slug of key or name
        candidate = title_name or title_key
        direct_tag = _clean_slug(candidate)

        # Quick check if direct tag returns posts
        url_direct = f"https://www.sakugabooru.com/post.json?tags={urllib.parse.quote(direct_tag)}&limit={limit}"
        req_direct = urllib.request.Request(url_direct, headers={"User-Agent": "AnimeParsing/2.0"})
        try:
            with urllib.request.urlopen(req_direct, timeout=6) as resp:
                direct_data = json.load(resp)
            if direct_data and isinstance(direct_data, list) and len(direct_data) > 0:
                tag = direct_tag
        except Exception:
            pass

        # 2. If direct tag yielded no posts, search tag API
        if not tag:
            tag = _find_sakugabooru_tag(candidate)

    if not tag:
        return []

    url = f"https://www.sakugabooru.com/post.json?tags={urllib.parse.quote(tag)}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "AnimeParsing/2.0"})

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
    except Exception as e:
        log.debug(f"Failed to fetch sakuga for tag {tag}: {e}")
        return []

    clips = []
    for item in data or []:
        if not isinstance(item, dict):
            continue
        file_url = item.get("file_url")
        if not file_url:
            continue
        post_id = item.get("id")
        raw_tags = (item.get("tags") or "").split()

        animators = [
            t.replace("_", " ").title()
            for t in raw_tags
            if t not in NON_ANIMATOR_TAGS and t != tag and not t.startswith("ep") and not t.isdigit()
        ]

        clips.append({
            "id": post_id,
            "file_url": file_url,
            "preview_url": item.get("preview_url") or item.get("sample_url"),
            "source": item.get("source"),
            "animators": animators[:3],
            "post_url": f"https://www.sakugabooru.com/post/show/{post_id}",
        })

    return clips
