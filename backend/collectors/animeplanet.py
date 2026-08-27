"""Anime-Planet scraper (static HTML, no key)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .web import curl_get

BASE = "https://www.anime-planet.com/anime/{slug}"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _bg_image(el) -> str | None:
    style = el.get("style") or ""
    m = re.search(r"url\((.+?)\)", style)
    if not m:
        return None
    raw = m.group(1)
    if "\\" in raw:
        raw = re.sub(r"\\([0-9A-Fa-f]{1,6})\s?", lambda mm: chr(int(mm.group(1), 16)), raw)
    return raw


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"Anime-Planet for {entry['planet_slug']}")
    url = BASE.format(slug=entry["planet_slug"])
    html = curl_get(url, retries=4)
    soup = BeautifulSoup(html, "lxml")

    result = {
        "source": "anime_planet",
        "slug": entry["planet_slug"],
        "url": url,
    }

    h1 = soup.select_one("h1")
    result["title"] = _clean(h1.get_text()) if h1 else None

    aka = soup.select_one("h2.aka")
    result["alt_titles"] = _clean(aka.get_text()) if aka else None

    syn = soup.select_one(".entrySynopsis")
    result["synopsis"] = _clean(syn.get_text(" ", strip=True)) if syn else None

    eb = soup.select_one("section.pure-g.entryBar")
    result["entry_bar"] = _clean(eb.get_text(" | ", strip=True)) if eb else None

    rating = soup.select_one(".avgRating")
    result["rating_text"] = _clean(rating.get_text(" ", strip=True)) if rating else None

    sb = soup.select_one("section.sidebarStats")
    result["user_stats"] = _clean(sb.get_text(" | ", strip=True)) if sb else None

    result["tags"] = [
        _clean(a.get_text()) for a in soup.select('a[href*="/anime/tags/"]')
    ]

    # characters
    chars = []
    for a in soup.select("a.CharacterCard[href*='/characters/']"):
        name = a.select_one(".CharacterCard__title")
        va = a.select_one(".CharacterCard__body")
        comments = a.select_one(".CharacterCard__comments__number")
        aside = a.select_one(".CharacterCard__aside")
        chars.append({
            "name": _clean(name.get_text()) if name else None,
            "voice_actor": _clean(va.get_text(" ", strip=True)) if va else None,
            "comments": _clean(comments.get_text()) if "js" not in str(comments) and comments else None,
            "image": _bg_image(aside) if aside else None,
            "url": urljoin(url, a.get("href") or ""),
            "character_id": a.get("data-character-id"),
        })
    result["characters"] = chars

    # staff
    staff_sec = soup.select_one("section.EntryPage__content__section__staff")
    staff = []
    if staff_sec:
        for a in staff_sec.select("a[href*='/people/']"):
            img = a.select_one("img")
            name_el = a.select_one("strong")
            staff.append({
                "name": _clean(name_el.get_text()) if name_el else _clean(a.get_text(" ", strip=True)),
                "role": None,
                "image": img.get("src") if img else _bg_image(a),
                "url": urljoin(url, a.get("href") or ""),
            })
    # dedupe consecutive blocks of people cards may repeat names/roles combos
    result["staff"] = staff

    # recommended ("If you like this anime...")
    reco = []
    for a in soup.select(".reco-tabs a[title]"):
        inner = BeautifulSoup(a.get("title") or "", "lxml")
        h5 = inner.select_one("h5")
        rating = inner.select_one(".ttRating")
        reco.append({
            "title": _clean(h5.get_text()) if h5 else None,
            "rating": _clean(rating.get_text()) if rating else None,
            "anime_url": urljoin(url, a.get("href") or ""),
        })
    result["recommendations"] = reco

    # related anime / manga grids
    related = {"anime": [], "manga": []}
    for h2 in soup.select("h2"):
        txt = _clean(h2.get_text()).lower()
        if txt not in ("related anime", "related manga"):
            continue
        sec = h2.find_next_sibling()
        items = []
        for a in (sec.select("a[href]") if sec else []):
            h5 = a.select_one("h5, .theme-font")
            li = a.select_one("ul.entryBar")
            items.append({
                "title": _clean(h5.get_text()) if h5 else _clean(a.get_text(" ", strip=True)),
                "meta": _clean(li.get_text(" | ", strip=True)) if li else None,
                "url": urljoin(url, a.get("href") or ""),
            })
        related["manga" if txt == "related manga" else "anime"] = items
    result["related"] = related

    # screenshots
    imgs = soup.select("div.gah.alignright.hdr img, img.screenshots")
    result["screenshots"] = [
        img.get("src") for img in imgs if img.get("src")
    ]

    h2s = [_clean(h.get_text()) for h in soup.select("h2")]
    result["section_headers"] = h2s
    return result