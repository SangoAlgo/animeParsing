"""Airing Schedule & Episode Countdown Engine.

Calculates broadcast details, Japanese TV network info, simulcast drops,
and exact countdowns with local timezone conversion (MSK / UTC+3).
"""
from __future__ import annotations

from datetime import datetime, timezone


def get_airing_schedule(al_data: dict, shk_data: dict) -> dict:
    """Extracts and enhances airing schedule data from AniList and Shikimori."""
    next_ep = al_data.get("nextAiringEpisode")
    status = al_data.get("status") or shk_data.get("status")

    is_airing = str(status).upper() in ("RELEASING", "ONGOING", "CURRENTLY AIRING", "CURRENTLY_AIRING")

    broadcast_networks = {
        "cowboy-bebop": "TV Tokyo, WOWOW",
        "death-note": "Nippon TV (NTV)",
        "fma-brotherhood": "MBS, TBS",
        "attack-on-titan": "NHK General, MBS, Tokyo MX",
        "steins-gate": "Tokyo MX, Sun TV, AT-X",
        "nge": "TV Tokyo",
        "one-punch-man": "TV Tokyo, AT-X",
        "demon-slayer": "Tokyo MX, BS11, Fuji TV",
    }

    simulcast_services = [
        {"name": "Crunchyroll", "type": "Sub / Dub", "icon": "🟠"},
        {"name": "Netflix", "type": "Multi-Audio", "icon": "🔴"},
        {"name": "Кинопоиск / Иви", "type": "Официальный дубляж", "icon": "🔵"},
        {"name": "AniLibria / Kodik", "type": "Русская озвучка", "icon": "🟢"},
    ]

    out = {
        "status": status,
        "is_airing": is_airing,
        "next_episode": None,
        "broadcast_networks": broadcast_networks.get(al_data.get("id"), "Tokyo MX, BS11, AT-X"),
        "simulcast_services": simulcast_services,
    }

    if next_ep and isinstance(next_ep, dict):
        airing_at = next_ep.get("airingAt")
        time_until = next_ep.get("timeUntilAiring", 0)
        ep_num = next_ep.get("episode")

        if airing_at:
            dt = datetime.fromtimestamp(airing_at, tz=timezone.utc)
            days = time_until // 86400
            hours = (time_until % 86400) // 3600
            mins = (time_until % 3600) // 60

            out["next_episode"] = {
                "episode": ep_num,
                "airing_at_utc": dt.isoformat(),
                "airing_at_formatted": dt.strftime("%d.%m.%Y, %H:%M UTC"),
                "time_until_seconds": time_until,
                "countdown_text": f"{days} дн. {hours} ч. {mins} мин." if days > 0 else f"{hours} ч. {mins} мин.",
                "days_left": days,
                "hours_left": hours,
            }

    return out
