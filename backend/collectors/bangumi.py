"""Bangumi (bgm.tv) collector. Public v0 API, UA required, no key."""
from __future__ import annotations

from .web import http_get_json, http_post_json

BASE = "https://api.bgm.tv"


def _get(path: str) -> dict:
    return http_get_json(f"{BASE}/{path}", retries=4,
                         ua="AnimeParsing/1.0 (data collector)")


def _resolve_id(entry: dict) -> int:
    resp = http_post_json(
        f"{BASE}/v0/search/subjects",
        {"keyword": entry["bangumi_search"], "filter": {"type": [2]}},
        ua="AnimeParsing/1.0 (data collector)", retries=4,
    )
    for sub in resp.get("data", []):
        name = (sub.get("name") or "").lower()
        name_cn = (sub.get("name_cn") or "").lower()
        q = entry["bangumi_search"].lower()
        if name == q or name_cn == q:
            return sub["id"]
    # fuzzy: first anime-type result whose name contains or is contained in search
    for sub in resp.get("data", []):
        name = (sub.get("name") or "").lower()
        q = entry["bangumi_search"].lower()
        if q in name or name in q:
            return sub["id"]
    raise RuntimeError(f"Bangumi: subject not found: {entry['en']}")


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"Bangumi for {entry['en']}")
    sid = _resolve_id(entry)
    result = {"source": "bangumi", "id": sid}

    sub = _get(f"v0/subjects/{sid}")
    # drop huge images field? keep as-is (max data)
    result["subject"] = sub

    try:
        eps = _get(f"v0/episodes?subject_id={sid}&limit=100")
        result["episodes"] = eps.get("data", []) if isinstance(eps, dict) else eps
    except Exception as e:
        result["episodes"] = {"error": str(e)}

    try:
        persons = _get(f"v0/subjects/{sid}/persons")
        result["persons"] = persons.get("data", []) if isinstance(persons, dict) else persons
    except Exception as e:
        result["persons"] = {"error": str(e)}

    try:
        characters = _get(f"v0/subjects/{sid}/characters")
        result["characters"] = (
            characters.get("data", []) if isinstance(characters, dict) else characters
        )
    except Exception as e:
        result["characters"] = {"error": str(e)}
    return result