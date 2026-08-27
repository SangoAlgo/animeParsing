"""Shikimori (Shiki) collector. Public REST API, only a User-Agent is required."""
from __future__ import annotations

import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from .web import http_get_json

BASE = "https://shikimori.one/api"
SHIKI_UA = "AnimeParsing/1.0 (data collector; contact: none)"


def _get(path: str) -> dict:
    return http_get_json(f"{BASE}/{path}", retries=3, timeout=15, ua=SHIKI_UA)


def _resolve_id(entry: dict) -> int:
    """Prefer verified shikimori id (== MAL id for these classics), fall back to search."""
    sid = entry.get("shiki_id") or entry.get("mal")
    if sid:
        return int(sid)
    candidates = [entry["en"], entry.get("jp", "")]
    best = None
    for q in candidates:
        if not q:
            continue
        try:
            resp = _get(f"animes?search={urllib.parse.quote(q)}&limit=8&order=ranked")
            for item in resp or []:
                name = (item.get("name") or "").lower()
                cand = q.lower()
                if name == cand:
                    return item["id"]
                if best is None and (cand in name or name in cand):
                    best = item["id"]
            if best is not None:
                return best
        except Exception:
            pass
    if best is not None:
        return best
    raise RuntimeError(f"Shikimori: title not found: {entry['en']}")


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"Shikimori for {entry['en']}")
    sid = _resolve_id(entry)
    result = {
        "source": "shikimori",
        "id": sid,
    }

    endpoints = {
        "anime": f"animes/{sid}",
        "roles": f"animes/{sid}/roles",
        "similar": f"animes/{sid}/similar",
        "related": f"animes/{sid}/related",
        "franchise": f"animes/{sid}/franchise",
        "external_links": f"animes/{sid}/external_links",
        "screenshots": f"animes/{sid}/screenshots",
    }

    def _fetch_endpoint(key, path):
        try:
            return key, _get(path)
        except Exception as e:
            return key, {"error": str(e)}

    with ThreadPoolExecutor(max_workers=7) as ex:
        futures = [ex.submit(_fetch_endpoint, k, p) for k, p in endpoints.items()]
        for fut in futures:
            key, val = fut.result()
            result[key] = val

    return result