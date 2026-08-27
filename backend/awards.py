"""Awards, Accolades & Hall of Fame Database.

Tracks official awards (Crunchyroll Anime Awards, Tokyo Anime Award Festival,
Japan Media Arts Festival, Kobe Animation) and historic chart milestones.
"""
from __future__ import annotations

AWARDS_DATABASE: dict[str, list[dict]] = {
    "cowboy-bebop": [
        {"year": 1999, "award": "Animation Kobe", "category": "Лучший ТВ-сериал года", "icon": "🏆"},
        {"year": 2000, "award": "Japan Media Arts Festival", "category": "Премия за мастерство анимации", "icon": "🎖️"},
        {"year": 2000, "award": "Seiun Award", "category": "Лучшее научно-фантастическое произведение", "icon": "🚀"},
        {"year": "All-Time", "award": "IGN / Rolling Stone", "category": "Топ-3 величайших аниме в истории", "icon": "⭐"},
    ],
    "death-note": [
        {"year": 2007, "award": "Tokyo Anime Award Festival", "category": "Лучший сценарий года", "icon": "📜"},
        {"year": 2007, "award": "Anime Expo", "category": "Лучший детективный сериал", "icon": "🔍"},
        {"year": "All-Time", "award": "MyAnimeList / AniList", "category": "#1 по популярности в мире", "icon": "👑"},
    ],
    "fma-brotherhood": [
        {"year": 2010, "award": "Anime Grand Prix", "category": "Аниме года (Anime of the Year)", "icon": "🏆"},
        {"year": 2011, "award": "Tokyo Anime Award", "category": "Лучшая анимация года", "icon": "🎨"},
        {"year": "All-Time", "award": "MyAnimeList", "category": "#1 в глобальном рейтинге более 10 лет подряд", "icon": "👑"},
    ],
    "attack-on-titan": [
        {"year": 2013, "award": "Newtype Anime Awards", "category": "Аниме года (Anime of the Year)", "icon": "🏆"},
        {"year": 2014, "award": "Tokyo Anime Award", "category": "Гран-при фестиваля", "icon": "🎖️"},
        {"year": 2022, "award": "Crunchyroll Anime Awards", "category": "Аниме года & Лучший опенинг", "icon": "🏆"},
        {"year": 2023, "award": "Hollywood Critics Association", "category": "Лучший международный анимационный сериал", "icon": "🌟"},
    ],
    "steins-gate": [
        {"year": 2011, "award": "Newtype Anime Awards", "category": "Лучший главный герой (Окабэ Ринтаро)", "icon": "🔬"},
        {"year": 2012, "award": "Tokyo Anime Award", "category": "Лучшая режиссура", "icon": "🎬"},
        {"year": "All-Time", "award": "MyAnimeList", "category": "#1 среди научно-фантастических сериалов", "icon": "⏱️"},
    ],
    "nge": [
        {"year": 1996, "award": "Anime Grand Prix", "category": "Гран-при: Лучшее аниме года", "icon": "🏆"},
        {"year": 1997, "award": "Japan Media Arts Festival", "category": "Специальный приз жюри за вклад в культуру", "icon": "🎖️"},
        {"year": 1997, "award": "Animation Kobe", "category": "Индивидуальная премия режиссёру Хидэаки Анно", "icon": "🌟"},
    ],
    "demon-slayer": [
        {"year": 2019, "award": "Crunchyroll Anime Awards", "category": "Аниме года (Anime of the Year)", "icon": "🏆"},
        {"year": 2020, "award": "Tokyo Anime Award", "category": "Лучшая анимация и саундтрек", "icon": "🎨"},
        {"year": 2021, "award": "Japan Academy Film Prize", "category": "Фильм года (Поезд «Бесконечный»)", "icon": "🎬"},
    ],
    "one-punch-man": [
        {"year": 2016, "award": "Tokyo Anime Award", "category": "Лучшая боевая хореография и анимация", "icon": "🥊"},
        {"year": 2016, "award": "Sugoi Japan Award", "category": "Гран-при в категории аниме", "icon": "🏆"},
    ],
    "spirited-away": [
        {"year": 2003, "award": "Academy Awards (Oscar)", "category": "Премия «Оскар» за лучший анимационный фильм", "icon": "🏆"},
        {"year": 2002, "award": "Berlin Film Festival", "category": "«Золотой медведь» (Главный приз)", "icon": "🐻"},
        {"year": 2002, "award": "Japan Academy Prize", "category": "Лучший фильм года", "icon": "🎖️"},
    ],
    "your-name": [
        {"year": 2016, "award": "Japan Academy Prize", "category": "Лучший сценарий и саундтрек года", "icon": "🎼"},
        {"year": 2016, "award": "Sitges Film Festival", "category": "Лучший анимационный фильм", "icon": "🏆"},
        {"year": 2017, "award": "Mainichi Film Awards", "category": "Гран-при анимации", "icon": "🌟"},
    ],
}


def get_awards(title_key: str) -> list[dict]:
    """Returns official awards and accolades for a given anime title."""
    return AWARDS_DATABASE.get(title_key, [])
