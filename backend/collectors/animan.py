"""Animan Master Aggregator.

Synthesizes data into a rich, comprehensive anime dossier:
- AniList: metadata, posters, rankings, score distribution, streaming episodes with thumbnails, next airing
- Shikimori: Russian names, synopsis, screenshots, franchise nodes, related works, fandubbers/fansubbers
- AnimeThemes: OP/ED/INS with direct audio streams and video links
- Manga: chapter mapping, continue-after guide, MangaDex chapter links
- Fillers: canon/filler episode classification
- Sakuga: key animation clips from Sakugabooru
- Discography: OST albums and Spotify streaming links
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from airing import get_airing_schedule
from aniskip import get_title_skips
from awards import get_awards
from discography import get_discography
from faq import get_anime_faq
from fillers import TYPE_LABELS_RU, get_filler_guide
from kodik import get_kodik_catalog
from seiyuu import enrich_voice_actor
from timestamps import get_episode_timestamps
from translator import translate_batch, translate_google, translate_soft
from verdict import get_verdict
from watch_order import get_watch_order

STATUS_RU = {
    "finished": "завершён",
    "finished_airing": "завершён",
    "released": "завершён",
    "currently airing": "выходит",
    "currently_airing": "выходит",
    "ongoing": "выходит",
    "airing": "выходит",
    "not_yet_aired": "анонс",
    "not_yet_released": "анонс",
    "anons": "анонс",
    "unreleased": "анонс",
    "cancelled": "отменён",
}

FORMAT_RU = {
    "tv": "ТВ-сериал",
    "tv_13": "ТВ-сериал",
    "tv_24": "ТВ-сериал",
    "tv_48": "ТВ-сериал",
    "movie": "фильм",
    "ova": "OVA",
    "ona": "ONA",
    "special": "спецвыпуск",
    "music": "клип",
}

ORIGIN_RU = {
    "manga": "манга",
    "light_novel": "ранобэ",
    "light novel": "ранобэ",
    "original": "оригинал",
    "novel": "роман",
    "visual_novel": "визуальная новелла",
    "visual novel": "визуальная новелла",
    "game": "игра",
    "video_game": "видеоигра",
    "4_koma_manga": "ёнкома",
    "4-koma manga": "ёнкома",
    "web_manga": "веб-манга",
    "other": "другое",
}

AGE_RATING_RU = {
    "g": "0+ (для всех)",
    "pg": "6+ (детское)",
    "pg_13": "13+ (подростки)",
    "r": "17+ (насилие)",
    "r_plus": "18+ (для взрослых)",
    "rx": "18+ (хентай)",
    "none": None,
}

SEASON_RU = {
    "winter": "Зима",
    "spring": "Весна",
    "summer": "Лето",
    "fall": "Осень",
}

ROLE_RU = {
    "MAIN": "главный",
    "SUPPORTING": "второстепенный",
    "BACKGROUND": "эпизодический",
    "главный герой": "главный",
    "второстепенный герой": "второстепенный",
    "эпизодический персонаж": "эпизодический",
}


def _strip_ru(text: str) -> str:
    t = text or ""
    t = re.sub(r"\[/?(?:anime|manga|character|person|spoiler|b|i|u|url)[^\]]*\]", "", t)
    t = t.replace("[[", "").replace("]]", "")
    t = re.sub(r"\s*\n\s*", "\n", t).strip()
    return t


def _strip_html(text: str) -> str:
    t = text or ""
    t = re.sub(r"<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _norm(s):
    if isinstance(s, (list, tuple)):
        s = " ".join(str(x) for x in s)
    return re.sub(r"[\s_\-—–.,'\"]+", "", (str(s or "")).lower())


def _uniq(seq):
    seen = set()
    out = []
    for x in seq:
        k = _norm(x)
        if x and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def _ln(s):
    if not s:
        return None
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", s):
        return "ja"
    if re.search(r"[\u0400-\u04ff]", s):
        if re.search(r"[іїєґІЇЄҐ]", s):
            return "uk"
        return "ru"
    return "en"


def _shiki_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"https://shikimori.one{path}"


""" ------------------------------------------------------------------ """


def build(title: dict, sakuga_clips: list[dict] | None = None) -> dict:
    key = title.get("key")
    src = title.get("sources", {})
    parts = {k: (v or {}) for k, v in src.items()}
    al = parts.get("anilist", {})
    shk_all = parts.get("shikimori", {})
    shk = shk_all.get("anime") or {}
    at = (parts.get("anime_themes", {}) or {}).get("anime") or {}
    mn = parts.get("manga", {})
    mn_parts = mn.get("parts") or {}
    mn_a = mn_parts.get("anilist") or {}
    mn_s = mn_parts.get("shikimori") or {}
    mn_md = mn_parts.get("mangadex") or {}

    ep_total = al.get("episodes") or shk.get("episodes")
    fillers = get_filler_guide(key, ep_total)
    ost = get_discography(key)
    shiki_id = shk.get("id") or al.get("idMal")
    kodik_catalog = get_kodik_catalog(shiki_id) if shiki_id else {}

    out = {
        "source": "animan",
        "meta": {
            "merged_sources": [
                k for k in ("anilist", "shikimori", "anime_themes", "manga")
                if k in parts
            ],
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "titles": _titles(al, shk, title.get("names", {}).get("en")),
        "posters": _posters(al, shk, mn_a, mn_s, mn_md),
        "banners": _banners(al, mn_a),
        "gallery": _gallery(shk_all, al),
        "promo_videos": _promos(shk, al),
        "facts": _facts(al, shk, shk_all),
        "scores": _scores(al, shk),
        "description": _description(al, shk),
        "content_guide": _content_guide(al, shk),
        "voiceover": _voiceover(shk),
        "fillers": fillers,
        "episodes": _episodes(al, shk, shk_all, fillers, title_key=key),
        "kodik": kodik_catalog,
        "characters": _characters(al, shk_all),
        "staff": _staff(al, shk_all),
        "themes": _themes(at),
        "discography": ost,
        "sakuga": sakuga_clips or [],
        "manga": _manga(title.get("manga_map") or {}, mn_a, mn_s, mn_md),
        "franchise": _franchise(shk_all, shk.get("id")),
        "watch_order": get_watch_order(key),
        "verdict": get_verdict(key),
        "awards": get_awards(key),
        "faq": get_anime_faq(key),
        "airing_schedule": get_airing_schedule(al, shk),
        "external_links": _external(al, shk_all),
        "trailer": _trailer(al, shk),
    }
    return out


""" ------------------------------------------------------------------ """
""" names                                                               """


def _titles(al, shk, fallback_en=None):
    names = []
    if shk.get("russian"):
        names.append({"name": shk["russian"], "lang": "ru", "from": "shikimori"})
    if shk.get("name"):
        names.append({"name": shk["name"], "lang": "en", "from": "shikimori"})
    if shk.get("japanese"):
        names.append({"name": shk["japanese"], "lang": "ja", "from": "shikimori"})
    for s in shk.get("synonyms") or []:
        names.append({"name": s, "lang": _ln(s) or "en", "from": "shikimori"})

    al_t = al.get("title") or {}
    if al_t.get("english"):
        names.append({"name": al_t["english"], "lang": "en", "from": "anilist"})
    if al_t.get("romaji"):
        names.append({"name": al_t["romaji"], "lang": "en", "from": "anilist"})
    if al_t.get("native"):
        names.append({"name": al_t["native"], "lang": "ja", "from": "anilist"})
    for s in al.get("synonyms") or []:
        names.append({"name": s, "lang": _ln(s) or "en", "from": "anilist"})

    seen = set()
    uniq = []
    for n in names:
        k = _norm(n["name"])
        if k and k not in seen:
            seen.add(k)
            uniq.append(n)

    ru_main = shk.get("russian")
    en_main = al_t.get("english") or al_t.get("romaji") or shk.get("name") or fallback_en
    ja_main = al_t.get("native") or shk.get("japanese")
    romaji_main = al_t.get("romaji") or shk.get("name") or fallback_en

    return {
        "main": {
            "ru": ru_main or en_main,
            "en": en_main,
            "ja": ja_main,
            "romaji": romaji_main,
        },
        "all": uniq,
    }


""" ------------------------------------------------------------------ """
""" posters & banners with multi-resolution tiers                      """


def _posters(al, shk, mn_a, mn_s, mn_md):
    out = []
    # 1. AniList High-Res Poster
    cov = al.get("coverImage") or {}
    cov_best = cov.get("extraLarge") or cov.get("large") or cov.get("medium")
    if cov_best:
        res = {}
        if cov.get("extraLarge"):
            res["extra_large"] = cov["extraLarge"]
        if cov.get("large"):
            res["large"] = cov["large"]
        if cov.get("medium"):
            res["medium"] = cov["medium"]

        out.append({
            "url": cov_best,
            "title": "Официальный постер аниме (AniList)",
            "source": "AniList",
            "type": "anime_poster",
            "color": cov.get("color"),
            "size": "extraLarge" if cov.get("extraLarge") else "large",
            "resolutions": res,
        })

    # 2. Shikimori Original Poster
    shk_im = shk.get("image") or {}
    shk_best = _shiki_url(shk_im.get("original") or shk_im.get("preview"))
    if shk_best:
        res = {}
        if shk_im.get("original"):
            res["original"] = _shiki_url(shk_im["original"])
        if shk_im.get("preview"):
            res["preview"] = _shiki_url(shk_im["preview"])
        if shk_im.get("x96"):
            res["x96"] = _shiki_url(shk_im["x96"])
        if shk_im.get("x48"):
            res["x48"] = _shiki_url(shk_im["x48"])

        out.append({
            "url": shk_best,
            "title": "Официальный постер аниме (Shikimori)",
            "source": "Shikimori",
            "type": "anime_poster",
            "size": "original",
            "resolutions": res,
        })

    # 3. MangaDex Volume Cover
    if mn_md.get("cover_url"):
        md_url = mn_md["cover_url"]
        res = {
            "original": md_url,
            "large_512": f"{md_url}.512.jpg" if not md_url.endswith(".512.jpg") else md_url,
            "thumb_256": f"{md_url}.256.jpg" if not md_url.endswith(".256.jpg") else md_url,
        }
        out.append({
            "url": md_url,
            "title": "Оригинальная обложка тома манги (MangaDex)",
            "source": "MangaDex",
            "type": "manga_cover",
            "size": "original",
            "resolutions": res,
        })

    # 4. AniList Manga Cover
    m_cov = mn_a.get("coverImage") or {}
    m_best = m_cov.get("extraLarge") or m_cov.get("large")
    if m_best and m_best != cov_best:
        res = {}
        if m_cov.get("extraLarge"):
            res["extra_large"] = m_cov["extraLarge"]
        if m_cov.get("large"):
            res["large"] = m_cov["large"]
        if m_cov.get("medium"):
            res["medium"] = m_cov["medium"]

        out.append({
            "url": m_best,
            "title": "Обложка манги (AniList)",
            "source": "AniList Manga",
            "type": "manga_cover",
            "color": m_cov.get("color"),
            "size": "extraLarge",
            "resolutions": res,
        })

    # 5. Shikimori Manga Cover
    m_shk_im = mn_s.get("image") or {}
    m_shk_best = _shiki_url(m_shk_im.get("original") or m_shk_im.get("preview"))
    if m_shk_best and m_shk_best != shk_best:
        res = {}
        if m_shk_im.get("original"):
            res["original"] = _shiki_url(m_shk_im["original"])
        if m_shk_im.get("preview"):
            res["preview"] = _shiki_url(m_shk_im["preview"])
        if m_shk_im.get("x96"):
            res["x96"] = _shiki_url(m_shk_im["x96"])
        if m_shk_im.get("x48"):
            res["x48"] = _shiki_url(m_shk_im["x48"])

        out.append({
            "url": m_shk_best,
            "title": "Обложка манги (Shikimori)",
            "source": "Shikimori Manga",
            "type": "manga_cover",
            "size": "original",
            "resolutions": res,
        })

    seen = set()
    uniq = []
    for p in out:
        if p["url"] and p["url"] not in seen:
            seen.add(p["url"])
            uniq.append(p)
    return uniq


def _banners(al, mn_a):
    out = []
    b_al = al.get("bannerImage")
    if b_al:
        out.append({
            "url": b_al,
            "title": "Широкоформатный арт-баннер аниме (AniList 1080p)",
            "source": "AniList",
            "resolutions": {
                "original": b_al,
            }
        })
    b_mn = mn_a.get("bannerImage")
    if b_mn and b_mn != b_al:
        out.append({
            "url": b_mn,
            "title": "Баннер первоисточника (AniList Manga)",
            "source": "AniList Manga",
            "resolutions": {
                "original": b_mn,
            }
        })
    return out


""" ------------------------------------------------------------------ """
""" gallery & screenshots                                               """


def _gallery(shk_all, al):
    screenshots = []
    for s in shk_all.get("screenshots") or []:
        if isinstance(s, dict):
            orig = _shiki_url(s.get("original"))
            prev = _shiki_url(s.get("preview"))
            if orig:
                screenshots.append({
                    "original": orig,
                    "preview": prev or orig,
                    "title": "Официальный кадр / скриншот",
                    "source": "Shikimori"
                })

    episode_stills = []
    for ep in al.get("streamingEpisodes") or []:
        if ep.get("thumbnail"):
            episode_stills.append({
                "original": ep["thumbnail"],
                "preview": ep["thumbnail"],
                "title": ep.get("title") or "Кадр эпизода",
                "source": ep.get("site", "Crunchyroll")
            })

    return {
        "screenshots": screenshots,
        "episode_stills": episode_stills,
        "total_count": len(screenshots) + len(episode_stills)
    }


def _promos(shk, al):
    out = []
    for v in shk.get("videos") or []:
        if isinstance(v, dict) and (v.get("player_url") or v.get("url")):
            out.append({
                "title": v.get("name") or "Трейлер / Промо",
                "url": v.get("url") or v.get("player_url"),
                "player_url": v.get("player_url"),
                "thumbnail": v.get("image_url"),
                "hosting": v.get("hosting"),
                "kind": v.get("kind"),
                "from": "shikimori",
            })
    trailer = al.get("trailer") or {}
    if trailer.get("id") and trailer.get("site") == "youtube":
        yt_url = f"https://www.youtube.com/watch?v={trailer['id']}"
        out.append({
            "title": "Официальный трейлер",
            "url": yt_url,
            "player_url": f"https://www.youtube.com/embed/{trailer['id']}",
            "thumbnail": trailer.get("thumbnail"),
            "hosting": "youtube",
            "kind": "trailer",
            "from": "anilist",
        })

    seen = set()
    uniq = []
    for p in out:
        u = p.get("url") or p.get("player_url")
        if u and u not in seen:
            seen.add(u)
            uniq.append(p)
    return uniq


""" ------------------------------------------------------------------ """
""" facts                                                               """


def _facts(al, shk, shk_all):
    fmt_raw = (al.get("format") or shk.get("kind") or "").lower()
    fmt_ru = FORMAT_RU.get(fmt_raw, fmt_raw.upper() if fmt_raw else None)

    status_raw = (shk.get("status") or al.get("status") or "").lower()
    status_ru = STATUS_RU.get(status_raw, status_raw)

    year = al.get("seasonYear")
    if not year and shk.get("aired_on"):
        year = shk["aired_on"][:4]

    season_en = (al.get("season") or "").lower()
    season_ru = SEASON_RU.get(season_en)
    if season_ru and year:
        season_display = f"{season_ru} {year}"
    elif season_ru:
        season_display = season_ru
    else:
        season_display = str(year) if year else None

    origin_raw = (al.get("source") or "").lower().replace(" ", "_")
    origin_ru = ORIGIN_RU.get(origin_raw, origin_raw)

    ep_total = al.get("episodes") or shk.get("episodes")
    ep_aired = shk.get("episodes_aired") or ep_total
    duration = al.get("duration") or shk.get("duration")

    studios = []
    for st in shk.get("studios") or []:
        if st.get("name"):
            studios.append(st["name"])
    for e in (al.get("studios") or {}).get("edges") or []:
        n = (e.get("node") or {}).get("name")
        if n:
            studios.append(n)
    studios = _uniq(studios)

    genres = []
    for g in shk.get("genres") or []:
        ru_g = g.get("russian") or g.get("name")
        if ru_g:
            genres.append(ru_g)
    for g in al.get("genres") or []:
        genres.append(g)
    genres = _uniq(genres)

    tags = []
    for t in al.get("tags") or []:
        tags.append({
            "name": t.get("name"),
            "category": t.get("category"),
            "rank": t.get("rank"),
            "is_spoiler": t.get("isGeneralSpoiler") or t.get("isMediaSpoiler"),
            "description": t.get("description"),
        })

    age_rating_code = (shk.get("rating") or "").lower()
    age_rating_ru = AGE_RATING_RU.get(age_rating_code, age_rating_code.upper() if age_rating_code else None)

    next_ep = al.get("nextAiringEpisode")

    return {
        "format": fmt_raw.upper() if fmt_raw else None,
        "format_ru": fmt_ru,
        "status": status_raw,
        "status_ru": status_ru,
        "episodes_total": ep_total,
        "episodes_aired": ep_aired,
        "duration_min": duration,
        "year": str(year) if year else None,
        "season_en": season_en,
        "season": season_display,
        "origin": origin_raw,
        "origin_ru": origin_ru,
        "studios": studios,
        "age_rating": age_rating_code,
        "age_rating_ru": age_rating_ru,
        "genres": genres,
        "tags": tags[:24],
        "next_airing": next_ep,
    }


""" ------------------------------------------------------------------ """
""" scores & statistics                                                 """


def _scores(al, shk):
    al_score = al.get("averageScore")
    shk_score = shk.get("score")

    shk_num = float(shk_score) if shk_score is not None else None
    al_num = float(al_score) / 10.0 if al_score is not None else None

    vals = [v for v in (shk_num, al_num) if v is not None]
    avg = round(sum(vals) / len(vals), 2) if vals else None

    rankings = []
    for r in al.get("rankings") or []:
        rankings.append({
            "rank": r.get("rank"),
            "type": r.get("type"),
            "context": r.get("context"),
            "all_time": r.get("allTime"),
            "year": r.get("year"),
        })

    stats = al.get("stats") or {}
    score_dist = stats.get("scoreDistribution") or []
    status_dist = stats.get("statusDistribution") or []

    return {
        "average": avg,
        "shikimori": {
            "score": shk_score,
            "rates_scores_stats": shk.get("rates_scores_stats") or [],
            "rates_statuses_stats": shk.get("rates_statuses_stats") or [],
        },
        "anilist": {
            "score": al_score,
            "mean_score": al.get("meanScore"),
            "popularity": al.get("popularity"),
            "favourites": al.get("favourites"),
            "trending": al.get("trending"),
            "rankings": rankings,
            "score_distribution": score_dist,
            "status_distribution": status_dist,
        },
    }


""" ------------------------------------------------------------------ """
""" description & content guide                                         """


def _description(al, shk):
    ru_shk = _strip_ru(shk.get("description")) or None
    en_al = _strip_html(al.get("description")) or None

    ru_trans = None
    if en_al:
        ru_trans = translate_google(en_al, sl="en", tl="ru")

    return {
        "ru": ru_shk or ru_trans or en_al,
        "ru_shikimori": ru_shk,
        "ru_translated": ru_trans,
        "en": en_al,
    }


def _content_guide(al, shk):
    age_code = (shk.get("rating") or "").lower()
    age_ru = AGE_RATING_RU.get(age_code, "Без ограничений")

    warnings = []
    for t in al.get("tags") or []:
        name = t.get("name", "").lower()
        if any(w in name for w in ("gore", "violence", "blood", "death", "psychological", "horror", "nudity", "suicide", "tragedy")):
            warnings.append(t.get("name"))

    return {
        "age_rating": age_code,
        "age_rating_ru": age_ru,
        "warnings": _uniq(warnings),
    }


def _voiceover(shk):
    return {
        "licensors": shk.get("licensors") or [],
        "fandubbers": shk.get("fandubbers") or [],
        "fansubbers": shk.get("fansubbers") or [],
    }


""" ------------------------------------------------------------------ """
""" episodes with AniList posters, streaming, and filler flags          """


def _episodes(al, shk, shk_all, fillers, pre_translated: list[str] | None = None, title_key: str = ""):
    ep_total = al.get("episodes") or shk.get("episodes")
    ep_aired = shk.get("episodes_aired") or ep_total
    next_ep = al.get("nextAiringEpisode")

    ep_fillers_map = fillers.get("episodes_map", {}) if fillers else {}

    streaming_raw = al.get("streamingEpisodes") or []
    items = []

    # Real AniSkip OP/ED frame-accurate timestamps
    mal_id = shk.get("id") or al.get("idMal")
    target_count = ep_total or len(streaming_raw) or 26
    aniskip_map = get_title_skips(mal_id, target_count) if mal_id else {}

    clean_titles = []
    ep_nums = []
    raw_titles = []
    for i, ep in enumerate(streaming_raw, 1):
        raw_title = ep.get("title") or f"Episode {i}"
        m = re.match(r"(?:Episode|Ep\.?)\s*(\d+)(?:\s*[-–:]\s*(.*))?", raw_title, re.IGNORECASE)
        ep_num = int(m.group(1)) if m and m.group(1) else i
        ep_name = m.group(2).strip() if m and m.group(2) else raw_title
        clean_titles.append(ep_name)
        ep_nums.append(ep_num)
        raw_titles.append(raw_title)

    if pre_translated and len(pre_translated) == len(clean_titles):
        translated = pre_translated
    elif clean_titles:
        translated = translate_batch(clean_titles, sl="en", tl="ru")
    else:
        translated = []

    for i, ep in enumerate(streaming_raw):
        ep_num = ep_nums[i]
        ep_en = clean_titles[i]
        ep_ru = translated[i] if i < len(translated) else ep_en
        raw_title = raw_titles[i]

        ftype = ep_fillers_map.get(str(ep_num), "canon")
        flabel = TYPE_LABELS_RU.get(ftype, "Канон")

        # Prefer real AniSkip verified timestamps, fallback to structured db
        real_skip = aniskip_map.get(ep_num)
        if real_skip and real_skip.get("has_real_timestamps"):
            ts = real_skip
        else:
            ts = get_episode_timestamps(title_key, ep_num) if title_key else None

        items.append({
            "number": ep_num,
            "title": ep_ru or ep_en,
            "title_ru": ep_ru or ep_en,
            "title_en": ep_en,
            "full_title": raw_title,
            "thumbnail": ep.get("thumbnail"),
            "url": ep.get("url"),
            "site": ep.get("site", "Crunchyroll"),
            "filler_type": ftype,
            "filler_label": flabel,
            "timestamps": ts,
        })

    if not items and ep_total:
        screenshots = shk_all.get("screenshots") or []
        for i in range(1, (ep_total or 0) + 1):
            thumb = None
            if i - 1 < len(screenshots):
                thumb = _shiki_url(screenshots[i - 1].get("original") or screenshots[i - 1].get("preview"))

            ftype = ep_fillers_map.get(str(i), "canon")
            flabel = TYPE_LABELS_RU.get(ftype, "Канон")

            real_skip = aniskip_map.get(i)
            if real_skip and real_skip.get("has_real_timestamps"):
                ts = real_skip
            else:
                ts = get_episode_timestamps(title_key, i) if title_key else None

            items.append({
                "number": i,
                "title": f"Серия {i}",
                "title_ru": f"Серия {i}",
                "title_en": f"Episode {i}",
                "full_title": f"Серия {i}",
                "thumbnail": thumb,
                "url": None,
                "site": None,
                "filler_type": ftype,
                "filler_label": flabel,
                "timestamps": ts,
            })

    return {
        "total": ep_total,
        "aired": ep_aired,
        "next_airing": next_ep,
        "items": items,
    }


""" ------------------------------------------------------------------ """
""" characters                                                          """


def _characters(al, shk_all):
    recs = {}
    order = []

    def get_or_create(key, en_name, native_name, ru_name, image, role, desc):
        k = _norm(key) or _norm(en_name) or _norm(ru_name)
        if not k:
            return None
        if k not in recs:
            recs[k] = {
                "names": {"en": en_name, "ja": native_name, "ru": ru_name},
                "role": role,
                "image": image,
                "description": desc,
                "voice_actors": [],
                "sources": [],
            }
            order.append(k)
        rec = recs[k]
        if ru_name and not rec["names"]["ru"]:
            rec["names"]["ru"] = ru_name
        if en_name and not rec["names"]["en"]:
            rec["names"]["en"] = en_name
        if native_name and not rec["names"]["ja"]:
            rec["names"]["ja"] = native_name
        if image and not rec["image"]:
            rec["image"] = image
        if desc and not rec["description"]:
            rec["description"] = desc
        if role and not rec["role"]:
            rec["role"] = role
        return rec

    for r in shk_all.get("roles") or []:
        if not isinstance(r, dict):
            continue
        ch = r.get("character") or {}
        if not isinstance(ch, dict) or (not ch.get("id") and not ch.get("name")):
            continue
        roles = r.get("roles_russian") or r.get("roles") or []
        role_label = roles[0] if roles else "персонаж"
        role_mapped = ROLE_RU.get(role_label.lower(), role_label)

        ch_im = ch.get("image") or {}
        im = _shiki_url(ch_im.get("original") or ch_im.get("preview"))

        rec = get_or_create(
            key=ch.get("name"),
            en_name=ch.get("name"),
            native_name=None,
            ru_name=ch.get("russian") or ch.get("name"),
            image=im,
            role=role_mapped,
            desc=None,
        )
        if rec:
            rec["sources"].append("shikimori")

    for e in (al.get("characters") or {}).get("edges") or []:
        node = e.get("node") or {}
        nm = node.get("name") or {}
        en = nm.get("full")
        ja = nm.get("native")
        im = (node.get("image") or {}).get("large")
        role_raw = e.get("role")
        role_mapped = ROLE_RU.get(role_raw, role_raw)
        desc = node.get("description")

        rec = get_or_create(
            key=en,
            en_name=en,
            native_name=ja,
            ru_name=None,
            image=im,
            role=role_mapped,
            desc=desc,
        )
        if not rec:
            continue
        rec["sources"].append("anilist")

        for va in e.get("voiceActors") or []:
            va_nm = va.get("name") or {}
            va_full = va_nm.get("full")
            enriched = enrich_voice_actor(va_full) if va_full else None
            rec["voice_actors"].append({
                "name": va_full,
                "name_ru": (enriched.get("name_ru") if enriched else None) or va_full,
                "native": va_nm.get("native") or (enriched.get("name_ja") if enriched else None),
                "image": (va.get("image") or {}).get("large") or (enriched.get("photo") if enriched else None),
                "language": "Japanese",
                "notable_roles": (enriched.get("notable_roles") if enriched else []) or [],
            })

    out = []
    for k in order:
        r = recs[k]
        ru = r["names"]["ru"]
        r["names"]["ru"] = ru or r["names"]["en"]
        r["sources"] = _uniq(r["sources"])
        r["voice_actors"] = r["voice_actors"][:2]
        out.append(r)

    out.sort(key=lambda x: (x["role"] != "главный", not x["image"]))
    return out


""" ------------------------------------------------------------------ """
""" staff                                                               """


def _staff(al, shk_all):
    recs = {}
    order = []

    def get_or_create(key, en_name, native_name, ru_name, image, role):
        k = _norm(key) or _norm(en_name)
        if not k:
            return None
        if k not in recs:
            recs[k] = {
                "name": en_name,
                "native": native_name,
                "ru": ru_name,
                "roles": [role] if role else [],
                "image": image,
                "sources": [],
            }
            order.append(k)
        rec = recs[k]
        if role and role not in rec["roles"]:
            rec["roles"].append(role)
        if image and not rec["image"]:
            rec["image"] = image
        if ru_name and not rec["ru"]:
            rec["ru"] = ru_name
        return rec

    for r in shk_all.get("roles") or []:
        if not isinstance(r, dict):
            continue
        p = r.get("person") or {}
        if not isinstance(p, dict) or not p.get("name"):
            continue
        p_im = p.get("image") or {}
        im = _shiki_url(p_im.get("original") or p_im.get("preview"))
        roles = r.get("roles_russian") or r.get("roles") or []
        role_label = roles[0] if roles else None

        rec = get_or_create(
            key=p.get("name"),
            en_name=p.get("name"),
            native_name=None,
            ru_name=p.get("russian") or p.get("name"),
            image=im,
            role=role_label,
        )
        if rec:
            rec["sources"].append("shikimori")

    for e in (al.get("staff") or {}).get("edges") or []:
        node = e.get("node") or {}
        nm = node.get("name") or {}
        en = nm.get("full")
        ja = nm.get("native")
        im = (node.get("image") or {}).get("large")
        role = e.get("role")

        rec = get_or_create(
            key=en,
            en_name=en,
            native_name=ja,
            ru_name=None,
            image=im,
            role=role,
        )
        if rec:
            rec["sources"].append("anilist")

    out = []
    for k in order:
        r = recs[k]
        ru = r["ru"]
        r["ru"] = ru or r["name"]
        r["sources"] = _uniq(r["sources"])
        r["roles"] = _uniq(r["roles"])
        out.append(r)

    out.sort(key=lambda x: not x["image"])
    return out


""" ------------------------------------------------------------------ """
""" themes (AnimeThemes)                                                """


def _themes(at):
    if not at:
        return []
    out = []
    for th in at.get("animethemes") or []:
        song = th.get("song") or {}
        artists = [a.get("name") for a in (song.get("artists") or []) if a.get("name")]
        entries = th.get("animethemeentries") or []
        rows = []
        for ent in entries:
            videos = []
            for v in ent.get("videos") or []:
                audio_link = None
                av = v.get("audio")
                if isinstance(av, dict):
                    audio_link = av.get("link")
                videos.append({
                    "link": v.get("link"),
                    "audio": audio_link,
                    "tags": v.get("tags"),
                    "resolution": v.get("resolution"),
                    "nc": bool(v.get("nc")) or "NC" in (v.get("tags") or ""),
                })
            rows.append({
                "episodes": ent.get("episodes"),
                "notes": ent.get("notes"),
                "version": ent.get("version"),
                "videos": videos,
            })
        out.append({
            "type": th.get("type"),
            "sequence": th.get("sequence"),
            "song": song.get("title"),
            "artists": artists,
            "entries": rows,
        })
    out.sort(key=lambda t: (0 if t["type"] == "OP" else 1 if t["type"] == "ED" else 2,
                            t["sequence"] or 0))
    return out


""" ------------------------------------------------------------------ """
""" manga adaptation section                                            """


def _manga(manga_map, mn_a, mn_s, mn_md):
    sources = {}
    if mn_a:
        cov = mn_a.get("coverImage") or {}
        sources["anilist"] = {
            "title": (mn_a.get("title") or {}).get("romaji") or (mn_a.get("title") or {}).get("english"),
            "chapters": mn_a.get("chapters"),
            "volumes": mn_a.get("volumes"),
            "status": mn_a.get("status"),
            "score": mn_a.get("averageScore"),
            "cover": cov.get("extraLarge") or cov.get("large"),
            "url": mn_a.get("siteUrl") or (f"https://anilist.co/manga/{mn_a['id']}" if mn_a.get("id") else None),
        }
    if mn_s:
        m_obj = mn_s.get("manga") or {}
        m_im = m_obj.get("image") or {}
        sources["shikimori"] = {
            "title": m_obj.get("name"),
            "title_ru": m_obj.get("russian") or m_obj.get("name"),
            "chapters": m_obj.get("chapters"),
            "volumes": m_obj.get("volumes"),
            "status": m_obj.get("status"),
            "score": m_obj.get("score"),
            "cover": _shiki_url(m_im.get("original") or m_im.get("preview")),
            "url": f"https://shikimori.one/mangas/{mn_s['id']}" if mn_s.get("id") else None,
        }
    if mn_md:
        sources["mangadex"] = {
            "chapters_en": mn_md.get("chapters_en_total"),
            "last_chapter": (mn_md.get("attributes") or {}).get("lastChapter"),
            "cover": mn_md.get("cover_url"),
            "url": f"https://mangadex.org/title/{mn_md['id']}" if mn_md.get("id") else None,
            "volumes_en": mn_md.get("volumes_en") or [],
        }

    return {
        "map": manga_map,
        "sources": sources,
    }


""" ------------------------------------------------------------------ """
""" franchise (EXCLUSIVELY from Shikimori)                              """


def _franchise(shk_all, current_anime_id):
    fran_raw = shk_all.get("franchise") or {}
    nodes_raw = fran_raw.get("nodes") or []
    links_raw = fran_raw.get("links") or []

    nodes = []
    for n in nodes_raw:
        im = n.get("image_url") or n.get("image")
        if im and "missing" in im:
            im = None
        nodes.append({
            "id": n.get("id"),
            "name": n.get("name"),
            "year": n.get("year"),
            "kind": FORMAT_RU.get((n.get("kind") or "").lower(), n.get("kind")),
            "image": _shiki_url(im),
            "url": f"https://shikimori.one/animes/{n.get('id')}" if n.get("id") else None,
            "is_current": n.get("id") == current_anime_id,
            "weight": n.get("weight", 0),
            "date": n.get("date"),
        })

    nodes.sort(key=lambda x: (x["year"] or 9999, x["date"] or 0))

    related = []
    for r in (shk_all.get("related") if isinstance(shk_all.get("related"), list) else []) or []:
        rel_ru = r.get("relation_russian") or r.get("relation") or "Связанное"
        for key in ("anime", "manga"):
            item = r.get(key)
            if not item:
                continue
            im = (item.get("image") or {}).get("original") or (item.get("image") or {}).get("preview")
            related.append({
                "relation": rel_ru,
                "format": key,
                "title": item.get("russian") or item.get("name"),
                "original_title": item.get("name"),
                "image": _shiki_url(im),
                "kind": FORMAT_RU.get((item.get("kind") or "").lower(), item.get("kind")),
                "score": item.get("score"),
                "url": f"https://shikimori.one/{'animes' if key == 'anime' else 'mangas'}/{item.get('id')}",
            })

    return {
        "nodes": nodes,
        "links": links_raw,
        "related": related,
    }


""" ------------------------------------------------------------------ """
""" external links & trailer                                            """


def _external(al, shk_all):
    out = []
    for l in al.get("externalLinks") or []:
        out.append({
            "site": l.get("site"),
            "url": l.get("url"),
            "kind": l.get("type") or "official",
            "language": l.get("language"),
            "icon": l.get("icon"),
            "color": l.get("color"),
            "from": "anilist",
        })
    for l in (shk_all.get("external_links") if isinstance(shk_all.get("external_links"), list) else []) or []:
        if isinstance(l, dict) and l.get("url"):
            out.append({
                "site": l.get("kind") or l.get("label"),
                "url": l["url"],
                "kind": "official",
                "language": None,
                "from": "shikimori",
            })

    seen = set()
    uniq = []
    for e in out:
        u = e.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(e)
    return uniq


def _trailer(al, shk):
    t = al.get("trailer") or {}
    if t.get("id") and t.get("site") == "youtube":
        return {
            "site": "youtube",
            "url": f"https://www.youtube.com/watch?v={t['id']}",
            "embed_url": f"https://www.youtube.com/embed/{t['id']}",
            "thumbnail": t.get("thumbnail"),
            "from": "anilist",
        }
    for v in shk.get("videos") or []:
        if isinstance(v, dict) and (v.get("player_url") or v.get("url")):
            return {
                "site": v.get("hosting", "youtube"),
                "url": v.get("url") or v.get("player_url"),
                "embed_url": v.get("player_url"),
                "thumbnail": v.get("image_url"),
                "from": "shikimori",
            }
    return None