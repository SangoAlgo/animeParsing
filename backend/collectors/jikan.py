"""Jikan v4 collector - official unofficial MyAnimeList API, public, no key.
The public instance sits behind Cloudflare and drops python urllib traffic
(TLS fingerprint), while curl passes - so we fetch via curl.exe."""
from __future__ import annotations

import json
import time

from .web import curl_get

BASE = "https://api.jikan.moe/v4"


def _get(path: str, timeout=60, retries=8):
    body = curl_get(f"{BASE}/{path}", timeout=timeout, retries=retries,
                    backoff=5.0, jitter=3.0)
    time.sleep(1.1)  # be polite to the public instance
    return json.loads(body.decode("utf-8", "replace"))


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"Jikan   (MyAnimeList) #{entry['mal']}")
    mid = entry["mal"]
    result = {"source": "jikan_myanimelist", "id": mid, "data": None}

    main = _get(f"anime/{mid}")
    result["data"] = main.get("data")

    extras = {
        "characters": f"anime/{mid}/characters",
        "staff": f"anime/{mid}/staff",
        "recommendations": f"anime/{mid}/recommendations",
        "pictures": f"anime/{mid}/pictures",
        "statistics": f"anime/{mid}/statistics",
        "themes": f"anime/{mid}/themes",
        "videos": f"anime/{mid}/videos",
        "episodes": f"anime/{mid}/episodes?page=1",
        "external": f"anime/{mid}/external",
    }
    for key, path in extras.items():
        try:
            result[key] = _get(path)
        except Exception as e:
            result[key] = {"error": str(e)}
    return result