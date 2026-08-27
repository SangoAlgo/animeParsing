"""Google Translate API integration with thread-safe disk cache and batch translation.

Translates English text (e.g. AniList descriptions, episode titles, character bios)
to Russian using Google Translate with persistent caching in data/translations.json.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import urllib.parse
import urllib.request

log = logging.getLogger("translator")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_PATH = os.path.join(DATA_DIR, "translations.json")

_cache = None
_lock = threading.Lock()


def _load():
    global _cache
    with _lock:
        if _cache is None:
            try:
                with open(CACHE_PATH, encoding="utf-8") as f:
                    _cache = json.load(f)
            except (OSError, ValueError):
                _cache = {}
        return dict(_cache)


def _set_cache(entries: dict[str, dict]):
    global _cache
    with _lock:
        if _cache is None:
            _cache = {}
        _cache.update(entries)
        try:
            tmp = CACHE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_cache, f, ensure_ascii=False, indent=2)
            try:
                os.replace(tmp, CACHE_PATH)
            except OSError:
                try:
                    os.remove(CACHE_PATH)
                except OSError:
                    pass
                os.replace(tmp, CACHE_PATH)
        except OSError:
            pass


def _key(text: str, sl: str = "en", tl: str = "ru") -> str:
    return hashlib.sha1(f"google|{sl}|{tl}|{text.strip()}".encode("utf-8")).hexdigest()


def translate_google(text: str, sl: str = "en", tl: str = "ru", timeout: int = 8) -> str:
    """Translate single text using Google Translate API with local caching."""
    text = (text or "").strip()
    if not text or len(text) < 2:
        return text

    cache = _load()
    k = _key(text, sl, tl)
    if k in cache and cache[k].get("translated"):
        return cache[k]["translated"]

    url = (
        "https://translate.googleapis.com/translate_a/single?"
        + urllib.parse.urlencode({
            "client": "gtx",
            "sl": sl,
            "tl": tl,
            "dt": "t",
            "q": text,
        })
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Animan/2.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        translated = "".join([part[0] for part in data[0] if part and part[0]]).strip()
        if translated:
            _set_cache({
                k: {
                    "translated": translated,
                    "original": text[:200],
                    "sl": sl,
                    "tl": tl,
                }
            })
            return translated
    except Exception as e:
        log.debug(f"Google Translate skipped for snippet '{text[:40]}...': {e}")

    return text


def translate_batch(texts: list[str], sl: str = "en", tl: str = "ru", batch_size: int = 30) -> list[str]:
    """Translate a list of strings (e.g. episode titles) efficiently using batch requests."""
    if not texts:
        return []

    cache = _load()
    results = [None] * len(texts)
    missing_indices = []
    missing_texts = []

    for i, t in enumerate(texts):
        clean = (t or "").strip()
        if not clean or len(clean) < 2:
            results[i] = clean
            continue
        k = _key(clean, sl, tl)
        if k in cache and cache[k].get("translated"):
            results[i] = cache[k]["translated"]
        else:
            missing_indices.append(i)
            missing_texts.append(clean)

    if not missing_texts:
        return results

    new_entries = {}

    # Process missing in batches
    for chunk_start in range(0, len(missing_texts), batch_size):
        chunk_texts = missing_texts[chunk_start:chunk_start + batch_size]
        chunk_indices = missing_indices[chunk_start:chunk_start + batch_size]

        combined = "\n".join(chunk_texts)
        url = (
            "https://translate.googleapis.com/translate_a/single?"
            + urllib.parse.urlencode({
                "client": "gtx",
                "sl": sl,
                "tl": tl,
                "dt": "t",
                "q": combined,
            })
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Animan/2.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            translated_combined = "".join([part[0] for part in data[0] if part and part[0]])
            translated_lines = translated_combined.split("\n")

            for orig, tr, orig_idx in zip(chunk_texts, translated_lines, chunk_indices):
                tr_clean = tr.strip() or orig
                results[orig_idx] = tr_clean
                new_entries[_key(orig, sl, tl)] = {
                    "translated": tr_clean,
                    "original": orig[:200],
                    "sl": sl,
                    "tl": tl,
                }
        except Exception as e:
            log.debug(f"Batch Google Translate skipped: {e}")
            for orig, orig_idx in zip(chunk_texts, chunk_indices):
                results[orig_idx] = orig

    if new_entries:
        _set_cache(new_entries)

    return results


def translate_soft(text: str, langpair=("en", "ru")) -> tuple[str, bool]:
    """Compatibility helper: returns (translated_text, was_translated_bool)."""
    sl, tl = langpair if len(langpair) == 2 else ("en", "ru")
    res = translate_google(text, sl=sl, tl=tl)
    return res, bool(res and res != text)