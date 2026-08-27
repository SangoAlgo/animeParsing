"""Manga collector: gathers the manga adaptation of each title from
the manga sources (MangaDex, AniList, Shikimori) with automatic adaptation discovery.
"""
from __future__ import annotations

import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from .web import http_get_json, http_post_json

log = logging.getLogger("manga")
SHIKI_UA = "AnimeParsing/1.0 (data collector; contact: none)"

ANILIST_Q = """
query ($id: Int) {
  Media(id: $id, type: MANGA) {
    id idMal title { romaji english native userPreferred } synonyms format status
    description siteUrl chapters volumes countryOfOrigin isAdult isLicensed
    startDate { year month day } endDate { year month day }
    averageScore meanScore popularity favourites trending
    coverImage { extraLarge large medium color } bannerImage genres
    tags { id name category rank isGeneralSpoiler isMediaSpoiler isAdult }
    relations { edges { relationType node { id type title { romaji english } format } } }
    staff (sort: [RELEVANCE, ID], perPage: 40) {
      edges { role node { id name { full native } language image { large } } }
    }
    characters (sort: [RELEVANCE, ROLE], perPage: 40) {
      edges { role node { id name { full native } image { large } } }
    }
    recommendations (page: 1, perPage: 20, sort: RATING) {
      nodes { rating mediaRecommendation { id title { romaji english } format } }
    }
    externalLinks { id site url type language color icon }
    rankings { id rank type format year season allTime context }
  }
}
"""


def _collect_anilist(manga_id: int, progress=None):
    if progress:
        progress(f"Manga/AniList #{manga_id}")
    data = http_post_json(
        "https://graphql.anilist.co",
        {"query": ANILIST_Q, "variables": {"id": manga_id}},
        retries=3,
        timeout=15,
    )
    media = (data.get("data") or {}).get("Media")
    if not media:
        raise RuntimeError(f"Manga/AniList: no data for id {manga_id}")
    result = {"source": "anilist", "id": media.get("id"), "fetched_at_utc": None}
    result.update(media)
    return result


def _collect_shikimori(shiki_manga_id: int, progress=None):
    if progress:
        progress(f"Manga/Shikimori #{shiki_manga_id}")
    sid = shiki_manga_id

    def get(path):
        return http_get_json(f"https://shikimori.one/api/{path}", retries=3, timeout=15, ua=SHIKI_UA)

    result = {"source": "shikimori", "id": sid}

    endpoints = {
        "manga": f"mangas/{sid}",
        "roles": f"mangas/{sid}/roles",
        "similar": f"mangas/{sid}/similar",
        "related": f"mangas/{sid}/related",
        "external_links": f"mangas/{sid}/external_links",
    }

    def _fetch(k, p):
        try:
            return k, get(p)
        except Exception as e:
            return k, {"error": str(e)}

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(_fetch, k, p) for k, p in endpoints.items()]
        for fut in futures:
            k, v = fut.result()
            result[k] = v

    return result


def _collect_mangadex_by_id(mid: str, progress=None):
    if progress:
        progress(f"Manga/MangaDex {mid}")

    def get(path):
        return http_get_json(f"https://api.mangadex.org/{path}", retries=3, timeout=15)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_full = ex.submit(get, f"manga/{mid}?includes[]=author&includes[]=artist&includes[]=cover_art")
        f_agg = ex.submit(get, f"manga/{mid}/aggregate?translatedLanguage[]=en")

        try:
            full = f_full.result()
        except Exception:
            full = {}
        try:
            agg = f_agg.result()
        except Exception:
            agg = {}

    raw = full.get("data") or {}
    attrs = dict(raw.get("attributes", {}))

    def rel_names(t):
        nodes = [r for r in raw.get("relationships", []) if r.get("type") == t]
        return [n.get("attributes", {}).get("name") for n in nodes]

    rels = {r.get("type"): r for r in raw.get("relationships", [])}
    cover_file = (rels.get("cover_art") or {}).get("attributes", {}).get("fileName")
    result = {
        "source": "mangadex",
        "id": mid,
        "attributes": attrs,
        "cover_url": (f"https://uploads.mangadex.org/covers/{mid}/{cover_file}.512.jpg" if cover_file else None),
        "authors": rel_names("author"),
        "artists": rel_names("artist"),
    }

    vols = agg.get("volumes") or {}
    chapters_by_volume = []
    total = 0
    for vol_no in sorted(vols, key=lambda v: (v is None, v)):
        v = vols[vol_no] or {}
        chs = sorted((v.get("chapters") or {}).keys())
        chapters_by_volume.append({
            "volume": v.get("volume"),
            "count": v.get("count", len(chs)),
            "chapters": [
                {"n": ch_no, "id": (v["chapters"][ch_no] or {}).get("id")}
                for ch_no in chs
            ],
        })
        total += v.get("count", len(chs))
    result["volumes_en"] = chapters_by_volume
    result["chapters_en_total"] = total
    return result


def _search_mangadex(title_name: str) -> str | None:
    """Searches MangaDex for a title and returns the best matching manga ID."""
    if not title_name:
        return None
    try:
        url = f"https://api.mangadex.org/manga?title={urllib.parse.quote(title_name)}&limit=3&order[relevance]=desc"
        data = http_get_json(url, retries=2, timeout=8)
        items = data.get("data") or []
        if items and isinstance(items, list):
            return items[0].get("id")
    except Exception:
        pass
    return None


def collect(entry: dict, progress=None) -> dict:
    """Gathers manga adaptation from MangaDex, AniList, and Shikimori."""
    pins = entry.get("manga") or {}
    title_name = entry.get("en") or entry.get("key")

    result = {
        "source": "manga",
        "pins": dict(pins),
        "parts": {},
        "errors": {},
    }

    # 1. Automatic MangaDex search if mid is missing
    mangadex_id = pins.get("mangadex")
    if not mangadex_id and title_name:
        mangadex_id = _search_mangadex(title_name)
        if mangadex_id:
            result["pins"]["mangadex"] = mangadex_id

    # 2. Fetch MangaDex if found
    if mangadex_id:
        try:
            result["parts"]["mangadex"] = _collect_mangadex_by_id(mangadex_id, progress=progress)
        except Exception as e:
            result["errors"]["mangadex"] = str(e)

    # 3. Fetch AniList Manga if pinned
    if pins.get("anilist"):
        try:
            result["parts"]["anilist"] = _collect_anilist(pins["anilist"], progress=progress)
        except Exception as e:
            result["errors"]["anilist"] = str(e)

    # 4. Fetch Shikimori Manga if pinned
    if pins.get("shiki"):
        try:
            result["parts"]["shikimori"] = _collect_shikimori(pins["shiki"], progress=progress)
        except Exception as e:
            result["errors"]["shikimori"] = str(e)

    return result