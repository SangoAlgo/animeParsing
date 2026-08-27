"""Kitsu collector (public JSON:API at kitsu.app/api/edge). No key needed."""
from __future__ import annotations

import urllib.parse

from .web import http_get_json

BASE = "https://kitsu.app/api/edge"
HDRS = {"Accept": "application/vnd.api+json"}


def _get(path_params: str) -> dict:
    return http_get_json(f"{BASE}/{path_params}", headers=HDRS, retries=4,
                         use_insecure_ssl=False)


def _anime_by_slug_or_id(spec, entry=None):
    if isinstance(spec, str):
        resp = _get(f"anime?filter[slug]={urllib.parse.quote(spec)}&page[limit]=1")
        if resp.get("data"):
            return resp["data"][0]
        if entry:  # fallback: text search, exact canonical title first
            found = None
            for q in dict.fromkeys([entry["en"], entry["jp"]]):
                s = _get(
                    f"anime?filter[text]={urllib.parse.quote(q)}&page[limit]=12"
                )
                for a in s.get("data", []):
                    ct = (a.get("attributes") or {}).get("canonicalTitle") or ""
                    if ct.lower() == q.lower():
                        return a
                    if found is None and q.lower() in ct.lower():
                        found = a
            if found:
                return found
        raise RuntimeError(f"Kitsu: no slug match for {spec}")
    resp = _get(f"anime/{spec}")
    return resp.get("data")


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"Kitsu   #{entry['kitsu_slug']}")
    anime = _anime_by_slug_or_id(entry["kitsu_slug"], entry)
    kid = anime["id"]

    ids = anime.get("relationships", {})
    include = ",".join(
        k for k in ("categories", "genres", "mediaRelationships", "streamingLinks")
        if k in ids
    )
    full = _get(f"anime/{kid}?include={include}")
    doc = dict(full)
    attrs = dict(doc["data"].get("attributes", {}))
    rels = doc.get("data", {}).get("relationships", {})
    incl = doc.get("included", [])

    def pick(type_name, key):
        items = []
        for inc in incl:
            if inc.get("type") == type_name:
                items.append(inc.get("attributes", {}))
        return items

    result = {
        "source": "kitsu",
        "id": kid,
        "attributes": attrs,
        "categories": pick("categories", "categories"),
        "genres": pick("genres", "genres"),
        "streamingLinks": pick("streamingLinks", "streamingLinks"),
        "mediaRelationships": pick("mediaRelationships", "mediaRelationships"),
        "relationship_ids": {k: v.get("data") for k, v in rels.items()},
    }

    # characters (first page, max 25) and voice actors
    try:
        ch = _get(f"anime/{kid}/characters?page[limit]=25&include=character,voices,castings")
        result["characters"] = ch.get("data", [])
        result["character_included"] = ch.get("included", [])
    except Exception:
        result["characters"] = []
        result["character_included"] = []

    # episodes (first 30)
    try:
        ep = _get(f"anime/{kid}/episodes?page[limit]=30")
        result["episodes"] = ep.get("data", [])
    except Exception:
        result["episodes"] = []

    # languages for titles/abbrev
    try:
        langs = _get(f"anime/{kid}/languages")
        result["languages"] = langs.get("data", [])
    except Exception:
        result["languages"] = []
    return result