"""AniSkip Real OP/ED/Recap Skip Timestamps Integration.

Fetches real, community-verified, frame-accurate opening and ending timestamps
from AniSkip API (https://api.aniskip.com) for video player skipping and fast-forwarding.
Caches all responses locally in data/aniskip_cache.json for instant offline access.
"""
from __future__ import annotations

import json
import os
import ssl
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "aniskip_cache.json")
_CACHE_LOCK = threading.Lock()
_CACHE_DATA: dict[str, dict] = {}


def _load_cache():
    global _CACHE_DATA
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                _CACHE_DATA = json.load(f)
        except Exception:
            _CACHE_DATA = {}
    else:
        _CACHE_DATA = {}


def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_CACHE_DATA, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_load_cache()


def fmt_seconds(s: float | int | None) -> str | None:
    if s is None:
        return None
    total_sec = int(round(s))
    m = total_sec // 60
    sec = total_sec % 60
    return f"{m:02d}:{sec:02d}"


def fetch_episode_skip(mal_id: int, episode: int, timeout: float = 6.0) -> dict | None:
    """Queries AniSkip API for a single episode and returns real skip intervals."""
    cache_key = f"{mal_id}_{episode}"
    with _CACHE_LOCK:
        if cache_key in _CACHE_DATA:
            return _CACHE_DATA[cache_key]

    url = (
        f"https://api.aniskip.com/v2/skip-times/{mal_id}/{episode}"
        "?types[]=op&types[]=ed&types[]=recap&types[]=mixed-op&types[]=mixed-ed&episodeLength=0"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Animan/2.0",
            "Accept": "application/json",
        },
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.load(resp)
            if not data.get("found"):
                result = {"found": False, "results": []}
            else:
                result = data
    except Exception:
        result = {"found": False, "results": []}

    with _CACHE_LOCK:
        _CACHE_DATA[cache_key] = result
        _save_cache()

    return result


def get_title_skips(mal_id: int | None, total_episodes: int = 26) -> dict[int, dict]:
    """Fetches all episode skip times for a given anime using concurrency."""
    if not mal_id or total_episodes <= 0:
        return {}

    ep_map = {}
    missing_eps = []

    with _CACHE_LOCK:
        for ep in range(1, total_episodes + 1):
            ck = f"{mal_id}_{ep}"
            if ck in _CACHE_DATA:
                ep_map[ep] = _parse_aniskip_results(_CACHE_DATA[ck], ep)
            else:
                missing_eps.append(ep)

    if missing_eps:
        def _worker(ep_num):
            res = fetch_episode_skip(mal_id, ep_num)
            return ep_num, _parse_aniskip_results(res, ep_num)

        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(_worker, ep) for ep in missing_eps]
            for fut in futures:
                try:
                    ep_num, parsed = fut.result()
                    ep_map[ep_num] = parsed
                except Exception:
                    pass

    return ep_map


def _parse_aniskip_results(raw_data: dict | None, episode_num: int) -> dict:
    if not raw_data or not raw_data.get("found"):
        return {
            "episode": episode_num,
            "has_real_timestamps": False,
            "op": None,
            "ed": None,
            "recap": None,
            "skip_intro": None,
            "skip_outro": None,
        }

    results = raw_data.get("results") or []
    op_item = None
    ed_item = None
    recap_item = None

    for r in results:
        stype = r.get("skipType", "").lower()
        inv = r.get("interval") or {}
        start_t = inv.get("startTime")
        end_t = inv.get("endTime")
        if start_t is None or end_t is None:
            continue

        item_obj = {
            "start_s": round(start_t, 2),
            "end_s": round(end_t, 2),
            "start_fmt": fmt_seconds(start_t),
            "end_fmt": fmt_seconds(end_t),
            "duration_s": round(end_t - start_t, 2),
            "skip_id": r.get("skipId"),
            "episode_length": r.get("episodeLength"),
        }

        if stype in ("op", "mixed-op") and not op_item:
            op_item = item_obj
        elif stype in ("ed", "mixed-ed") and not ed_item:
            ed_item = item_obj
        elif stype == "recap" and not recap_item:
            recap_item = item_obj

    return {
        "episode": episode_num,
        "has_real_timestamps": bool(op_item or ed_item),
        "source": "AniSkip (Real Verified Timestamps)",
        "op": op_item,
        "ed": ed_item,
        "recap": recap_item,
        "skip_intro": {"from": op_item["start_s"], "to": op_item["end_s"]} if op_item else None,
        "skip_outro": {"from": ed_item["start_s"], "to": ed_item["end_s"]} if ed_item else None,
    }
