"""Seiyuu (Voice Actor) Cross-Links & Notable Roles Knowledge Base.

Enriches character voice actors with high-res photos, Japanese & Russian names,
and their other iconic roles across top anime for deep cross-discovery.
"""
from __future__ import annotations

SEIYUU_DATABASE: dict[str, dict] = {
    "Mamoru Miyano": {
        "name_ru": "Мамору Мияно",
        "name_ja": "宮野 真守",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95095-2gD6i7v4uG3c.png",
        "notable_roles": [
            {"character": "Ягами Лайт", "anime": "Тетрадь Смерти", "icon": "📓"},
            {"character": "Окабэ Ринтаро", "anime": "Врата Штейна", "icon": "🔬"},
            {"character": "Осаму Дадзай", "anime": "Великий из бродячих псов", "icon": "📖"},
            {"character": "Линг Яо", "anime": "Стальной алхимик: Братство", "icon": "👑"},
        ],
    },
    "Koichi Yamadera": {
        "name_ru": "Коити Ямадэра",
        "name_ja": "山寺 宏一",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95015-lC7i1QcMfvE4.png",
        "notable_roles": [
            {"character": "Спайк Шпигель", "anime": "Ковбой Бибоп", "icon": "🚀"},
            {"character": "Рёдзи Кадзи", "anime": "Евангелион", "icon": "🍉"},
            {"character": "Бирус", "anime": "Dragon Ball Super", "icon": "🌌"},
        ],
    },
    "Megumi Ogata": {
        "name_ru": "Мэгуми Огата",
        "name_ja": "緒方 恵美",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95116-f3ZkK79hH8Vb.png",
        "notable_roles": [
            {"character": "Синдзи Икари", "anime": "Евангелион", "icon": "🤖"},
            {"character": "Юта Оккоцу", "anime": "Магическая битва 0", "icon": "💍"},
            {"character": "Макото Наэги", "anime": "Danganronpa", "icon": "⚖️"},
        ],
    },
    "Romi Park": {
        "name_ru": "Роми Пак",
        "name_ja": "朴 璐美",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95082-xOQ2yM3c5Vw1.png",
        "notable_roles": [
            {"character": "Эдвард Элрик", "anime": "Стальной алхимик", "icon": "🦾"},
            {"character": "Ханджи Зоэ", "anime": "Атака Титанов", "icon": "👓"},
            {"character": "Тосиро Хицугая", "anime": "Блич", "icon": "❄️"},
        ],
    },
    "Rie Kugimiya": {
        "name_ru": "Риэ Кугимия",
        "name_ja": "釘宮 理恵",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95008-sE0gXW5yG4L9.png",
        "notable_roles": [
            {"character": "Альфонс Элрик", "anime": "Стальной алхимик", "icon": "🛡️"},
            {"character": "Тайга Айсака", "anime": "Торадора!", "icon": "🐯"},
            {"character": "Кагура", "anime": "Гинтама", "icon": "☂️"},
        ],
    },
    "Yuki Kaji": {
        "name_ru": "Юки Кадзи",
        "name_ja": "梶 裕貴",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95672-YmX6f5q4L3P0.png",
        "notable_roles": [
            {"character": "Эрен Йегер", "anime": "Атака Титанов", "icon": "⚔️"},
            {"character": "Шото Тодороки", "anime": "Моя геройская академия", "icon": "🔥"},
            {"character": "Мелиодас", "anime": "Семь смертных грехов", "icon": "🗡️"},
            {"character": "Сверхзвуковой Соник", "anime": "Ванпанчмен", "icon": "💨"},
        ],
    },
    "Hiroshi Kamiya": {
        "name_ru": "Хироси Камия",
        "name_ja": "神谷 浩史",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95118-pL2t3V5w8N1Q.png",
        "notable_roles": [
            {"character": "Леви Аккерман", "anime": "Атака Титанов", "icon": "🧹"},
            {"character": "Трафальгар Ло", "anime": "One Piece", "icon": "⚓"},
            {"character": "Ято", "anime": "Бездомный бог (Noragami)", "icon": "🪙"},
            {"character": "Коёми Арараги", "anime": "Истории монстров (Monogatari)", "icon": "🧛"},
        ],
    },
    "Natsuki Hanae": {
        "name_ru": "Нацуки Ханаэ",
        "name_ja": "花江 夏樹",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n114256-kK7f5m2L3q0P.png",
        "notable_roles": [
            {"character": "Тандзиро Камадо", "anime": "Клинок, рассекающий демонов", "icon": "🌊"},
            {"character": "Кен Канеки", "anime": "Токийский гуль", "icon": "☕"},
            {"character": "Фалко Грайс", "anime": "Атака Титанов", "icon": "🦅"},
        ],
    },
    "Makoto Furukawa": {
        "name_ru": "Макото Фурукава",
        "name_ja": "古川 慎",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n114972-jK3m5L2q0P1Q.png",
        "notable_roles": [
            {"character": "Сайтама", "anime": "Ванпанчмен", "icon": "🥊"},
            {"character": "Миюки Сироганэ", "anime": "Госпожа Кагуя", "icon": "❤️"},
            {"character": "Тайдзю Оки", "anime": "Доктор Стоун", "icon": "🧪"},
        ],
    },
    "Kappei Yamaguchi": {
        "name_ru": "Каппэй Ямагути",
        "name_ja": "山口 勝平",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95067-qL2t3V5w8N1Q.png",
        "notable_roles": [
            {"character": "L (Эл Лоулайт)", "anime": "Тетрадь Смерти", "icon": "🍰"},
            {"character": "Усопп", "anime": "One Piece", "icon": "🎯"},
            {"character": "Инуяся", "anime": "Инуяся", "icon": "🐕"},
        ],
    },
    "Asami Imai": {
        "name_ru": "Асами Имаи",
        "name_ja": "今井 麻美",
        "photo": "https://s4.anilist.co/file/anilistcdn/staff/large/n95574-zK3m5L2q0P1Q.png",
        "notable_roles": [
            {"character": "Курису Макисэ", "anime": "Врата Штейна", "icon": "🧪"},
            {"character": "Тихая Кисараги", "anime": "THE iDOLM@STER", "icon": "🎤"},
        ],
    },
}


def enrich_voice_actor(va_name: str | None) -> dict | None:
    """Returns enriched seiyuu profile if present in database."""
    if not va_name:
        return None
    for name, data in SEIYUU_DATABASE.items():
        if name.lower() in va_name.lower() or va_name.lower() in name.lower():
            return {
                "name_en": name,
                "name_ru": data["name_ru"],
                "name_ja": data["name_ja"],
                "photo": data["photo"],
                "notable_roles": data["notable_roles"],
            }
    return None
