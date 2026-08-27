"""Kodik API Provider, Catalog Builder, and On-Demand Stream Resolver.

Ported from AnimeEpisodesParsing/kodik.
Features:
- Search by shikimori_id across Kodik API tokens
- Catalog structuring (studios/fandubs, seasons, episodes, permanent iframe links, screenshots)
- On-Demand Stream Resolver: extracts urlParams/vInfo from iframe, posts to /ftor, decodes rot18-base64 direct .m3u8 URLs
- In-memory caching for resolved links and catalog
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from urllib.parse import unquote, urlparse
import requests

log = logging.getLogger("kodik")

TOKENS = [
    os.getenv("KODIK_TOKEN_1", "56a768d08f43091901c44b54fe970049"),
    os.getenv("KODIK_TOKEN_2", "41dd95f84c21719b09d6c71182237a25"),
    os.getenv("KODIK_TOKEN_3", "77b567ec164db6ca9162d2f3dc4948c3"),
    os.getenv("KODIK_TOKEN_LEGACY", "447d179e875efe44217f20d1ee2146be"),
]

BASES = [
    "https://kodik-api.com",
    "https://kodikapi.com",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# Cache: link -> { "at": timestamp, "expires_at": timestamp, "data": dict }
_resolve_cache: dict[str, dict] = {}
_catalog_cache: dict[str, dict] = {}
RESOLVE_TTL = 12 * 3600  # 12 hours
CATALOG_TTL = 24 * 3600  # 24 hours


def decode_kodik_url(url: str) -> str:
    """Decodes Kodik rot18 + base64 obfuscated stream URL."""
    if not url:
        return ""
    if url.endswith(".m3u8"):
        return url if url.startswith("https") else f"https:{url}"
    b64 = ""
    for ch in url:
        if "A" <= ch <= "Z":
            b64 += chr(((ord(ch) - 65 + 18) % 26) + 65)
        elif "a" <= ch <= "z":
            b64 += chr(((ord(ch) - 97 + 18) % 26) + 97)
        else:
            b64 += ch
    if not b64.endswith("=="):
        b64 += "=="
    try:
        dec = base64.b64decode(b64).decode("utf-8")
        return dec if dec.startswith("https") else f"https:{dec}"
    except Exception:
        return url


def normalize_screenshots(val) -> list[str]:
    if not isinstance(val, list):
        return []
    res = []
    for s in val:
        src = s if isinstance(s, str) else (s.get("src") if isinstance(s, dict) else None)
        if src and re.match(r"^https?://", src, re.IGNORECASE):
            res.append(src)
    return res


def build_catalog_payload(items: list[dict]) -> dict[str, dict]:
    """Transforms raw Kodik search results into structured voiceover studios & episodes."""
    by_voice: dict[str, dict] = {}

    for item in items:
        t = item.get("translation")
        if not t or not isinstance(t, dict):
            continue
        v_title = t.get("title") or "Оригинал"
        v_type = "subtitles" if t.get("type") == "subtitles" else "voice"
        v_key = f"{v_title}|{v_type}"

        if v_key not in by_voice:
            by_voice[v_key] = {
                "name": v_title,
                "type": v_type,
                "by_season": {},
            }
        voice = by_voice[v_key]

        seasons = item.get("seasons") or {}
        fallback_link = item.get("link")

        for s_str, s_data in seasons.items():
            try:
                s_num = int(s_str)
            except (ValueError, TypeError):
                continue
            if s_num not in voice["by_season"]:
                voice["by_season"][s_num] = {}
            eps = voice["by_season"][s_num]

            ep_dict = (s_data.get("episodes") if isinstance(s_data, dict) else {}) or {}
            for e_str, e in ep_dict.items():
                try:
                    e_num = int(e_str)
                except (ValueError, TypeError):
                    continue
                link = (e.get("link") if isinstance(e, dict) else None) or fallback_link
                if not link:
                    continue
                if link.startswith("//"):
                    link = "https:" + link
                screenshots = normalize_screenshots(e.get("screenshots") if isinstance(e, dict) else None)
                eps[str(e_num)] = {
                    "link": link,
                    "screenshots": screenshots,
                    "skipbuttons": {"opening": None, "ending": None},
                }

        # Movie / OVA without seasons dict
        if not seasons and fallback_link:
            if 1 not in voice["by_season"]:
                voice["by_season"][1] = {}
            eps = voice["by_season"][1]
            if "1" not in eps:
                f_link = "https:" + fallback_link if fallback_link.startswith("//") else fallback_link
                eps["1"] = {
                    "link": f_link,
                    "screenshots": [],
                    "skipbuttons": {"opening": None, "ending": None},
                }

    payload: dict[str, dict] = {}
    for voice in by_voice.values():
        season_nums = sorted(voice["by_season"].keys())
        multi_season = len(season_nums) > 1
        for s_num in season_nums:
            eps = voice["by_season"][s_num]
            if not eps:
                continue
            key = f"{voice['name']} (Сезон {s_num})" if multi_season else voice["name"]
            entry = {
                "name": voice["name"],
                "episodes": eps,
                "is_active": True,
                "season": s_num,
                "type": voice["type"],
                "episodes_count": len(eps),
            }
            if key in payload:
                payload[key]["episodes"].update(entry["episodes"])
            else:
                payload[key] = entry

    return payload


def search_by_shikimori_id(shikimori_id: str | int, limit: int = 100) -> list[dict]:
    """Queries Kodik API for anime by shikimori_id."""
    shiki_str = str(shikimori_id).strip()
    if not shiki_str:
        return []

    for base in BASES:
        for token in TOKENS:
            try:
                url = f"{base}/search"
                resp = requests.get(
                    url,
                    params={
                        "token": token,
                        "shikimori_id": shiki_str,
                        "limit": limit,
                        "with_episodes_data": "true",
                        "prioritize_translation_type": "voice",
                    },
                    headers=HEADERS,
                    timeout=8,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results")
                    if isinstance(results, list) and len(results) > 0:
                        return results
            except Exception as e:
                log.debug("Kodik search attempt failed: %s (%s)", base, e)
                continue
    return []


def get_kodik_catalog(shikimori_id: str | int, fresh: bool = False) -> dict[str, dict]:
    """Fetches and builds Kodik catalog with caching."""
    shiki_str = str(shikimori_id).strip()
    now = time.time()

    if not fresh and shiki_str in _catalog_cache:
        c = _catalog_cache[shiki_str]
        if now - c["at"] < CATALOG_TTL:
            return c["payload"]

    raw = search_by_shikimori_id(shiki_str)
    catalog = build_catalog_payload(raw)
    if catalog:
        _catalog_cache[shiki_str] = {"at": now, "payload": catalog}
    return catalog


def parse_kodik_skip_button_str(skip_str: str) -> list[dict]:
    """Parses Kodik's parseSkipButton string (e.g. '1:43-3:13,21:09-23:20')."""
    if not skip_str:
        return []

    def time_to_sec(t_str: str) -> float:
        parts = t_str.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(parts[0])

    skips = []
    for idx, segment in enumerate(skip_str.split(",")):
        seg = segment.strip()
        if "-" in seg:
            p = seg.split("-")
            try:
                start_s = time_to_sec(p[0])
                end_s = time_to_sec(p[1])
                sk_type = "op" if idx == 0 else "ed"
                skips.append({
                    "start": start_s,
                    "end": end_s,
                    "type": sk_type,
                })
            except Exception:
                pass
    return skips


def extract_skips_from_kodik_html(html: str) -> list[dict]:
    """Extracts skips embedded in Kodik HTML playerSettings (e.g. parseSkipButton)."""
    m = re.search(r'parseSkipButton\s*\(\s*["\']([^"\']+)["\']', html)
    if m:
        return parse_kodik_skip_button_str(m.group(1))
    m2 = re.search(r'playerSettings\.skipButton\s*=\s*["\']([^"\']+)["\']', html)
    if m2:
        return parse_kodik_skip_button_str(m2.group(1))
    return []


def resolve_kodik_stream(
    iframe_url: str,
    fresh: bool = False,
    title_key: str | None = None,
    ep_num: int = 1,
    mal_id: int | str | None = None,
) -> dict | None:
    """On-Demand JIT Stream Resolver for Kodik player iframe."""
    if not iframe_url:
        return None
    canonical_url = ("https:" + iframe_url) if iframe_url.startswith("//") else iframe_url
    now = time.time()

    if not fresh and canonical_url in _resolve_cache:
        cached = _resolve_cache[canonical_url]
        if now - cached["at"] < RESOLVE_TTL and (cached.get("expires_at") or now + 600) > now:
            res = dict(cached["data"])
            res["cached"] = True
            return res

    try:
        resp = requests.get(canonical_url, headers=HEADERS, timeout=8)
        html = resp.text
        if "не найден" in html or "Видео удалено" in html:
            return None

        # 1. Extract skips embedded directly in Kodik HTML page
        html_skips = extract_skips_from_kodik_html(html)

        url_params_raw = re.search(r"var urlParams = '([^']*)'", html)
        if not url_params_raw:
            return None

        up = json.loads(unquote(url_params_raw.group(1)))
        v_type = re.search(r"vInfo\.type\s*=\s*'([^']+)'", html)
        v_hash = re.search(r"vInfo\.hash\s*=\s*'([^']+)'", html)
        v_id = re.search(r"vInfo\.id\s*=\s*'([^']+)'", html)

        if not (v_type and v_hash and v_id):
            return None

        params = {
            "d": up.get("d"),
            "d_sign": up.get("d_sign"),
            "pd": up.get("pd"),
            "pd_sign": up.get("pd_sign"),
            "ref": up.get("ref"),
            "ref_sign": up.get("ref_sign"),
            "bad_user": "false",
            "type": v_type.group(1),
            "hash": v_hash.group(1),
            "id": v_id.group(1),
            "info": "{}",
            "cdn_is_working": "true",
        }

        netloc = urlparse(canonical_url).netloc
        post_headers = {
            "Origin": f"https://{netloc}",
            "Referer": canonical_url,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": HEADERS["User-Agent"],
        }

        api_url = f"https://{netloc}/ftor"
        ftor_res = requests.post(api_url, data=params, headers=post_headers, timeout=8)
        ftor_data = ftor_res.json()

        links: dict[str, dict] = {}
        for q, entries in ftor_data.get("links", {}).items():
            if entries and isinstance(entries, list) and len(entries) > 0:
                first = entries[0]
                if "src" in first:
                    decoded = decode_kodik_url(first["src"])
                    if decoded:
                        links[str(q)] = {
                            "Src": decoded,
                            "Type": first.get("type", "application/x-mpegURL"),
                        }

        if not links:
            return None

        # 2. Extract skips from /ftor response
        ftor_skips = []
        skips_raw = ftor_data.get("skips") or []
        if isinstance(skips_raw, list):
            for sk in skips_raw:
                if isinstance(sk, dict) and "start" in sk and "end" in sk:
                    ftor_skips.append({"start": float(sk["start"]), "end": float(sk["end"]), "type": sk.get("type", "op" if not ftor_skips else "ed")})
                elif isinstance(sk, (list, tuple)) and len(sk) >= 2:
                    ftor_skips.append({"start": float(sk[0]), "end": float(sk[1]), "type": "op" if not ftor_skips else "ed"})

        # Combine real Kodik skips (HTML skipButton or /ftor)
        skips = html_skips or ftor_skips

        # 3. Fallback to AniSkip verified database if Kodik skips are missing
        if not skips or len(skips) < 2:
            from timestamps import get_episode_timestamps
            ts = get_episode_timestamps(title_key, ep_num, mal_id=mal_id)
            if not skips:
                skips = []
                if ts.get("op"):
                    skips.append({"start": float(ts["op"]["start_s"]), "end": float(ts["op"]["end_s"]), "type": "op"})
                if ts.get("ed"):
                    skips.append({"start": float(ts["ed"]["start_s"]), "end": float(ts["ed"]["end_s"]), "type": "ed"})
            elif len(skips) == 1 and ts.get("ed"):
                skips.append({"start": float(ts["ed"]["start_s"]), "end": float(ts["ed"]["end_s"]), "type": "ed"})

        result = {
            "link": canonical_url,
            "iframeUrl": canonical_url,
            "iframeCode": f'<iframe src="{canonical_url}" width="100%" height="100%" frameborder="0" allowfullscreen allow="autoplay *; fullscreen *"></iframe>',
            "links": links,
            "skips": skips,
            "cached": False,
            "resolvedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        _resolve_cache[canonical_url] = {
            "at": now,
            "expires_at": now + RESOLVE_TTL,
            "data": result,
        }
        return result

    except Exception as e:
        log.warning("Failed to resolve Kodik stream for %s: %s", canonical_url, e)
        return None
