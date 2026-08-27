"""The 10 titles to collect, with source IDs/pins for the 4 core sources:
AniList, Shikimori (via MAL id), AnimeThemes (via title search), and Manga (AniList, Shikimori, MangaDex).
"""

TITLES = [
    {
        "key": "cowboy-bebop",
        "en": "Cowboy Bebop",
        "jp": "カウボーイビバップ",
        "aliases": ["Cowboy Bebop"],
        "mal": 1,
        "anilist": 1,
        "manga": {
            "anilist": 30173,
            "shiki": 173,
            "mangadex": "46e782ea-478a-4204-b83b-8da011c73ba5",
        },
    },
    {
        "key": "death-note",
        "en": "Death Note",
        "jp": "デスノート",
        "aliases": ["Death Note", "DEATH NOTE"],
        "mal": 1535,
        "anilist": 1535,
        "manga": {
            "anilist": 30021,
            "shiki": 21,
            "mangadex": "75ee72ab-c6bf-4b87-badd-de839156934c",
        },
    },
    {
        "key": "fma-brotherhood",
        "en": "Fullmetal Alchemist: Brotherhood",
        "jp": "鋼の錬金術師 FULLMETAL ALCHEMIST",
        "aliases": ["Fullmetal Alchemist: Brotherhood", "Hagane no Renkinjutsushi"],
        "mal": 5114,
        "anilist": 5114,
        "manga": {
            "anilist": 30025,
            "shiki": 25,
            "mangadex": "dd8a907a-3850-4f95-ba03-ba201a8399e3",
        },
    },
    {
        "key": "attack-on-titan",
        "en": "Attack on Titan",
        "jp": "進撃の巨人",
        "aliases": ["Attack on Titan", "Shingeki no Kyojin"],
        "mal": 16498,
        "anilist": 16498,
        "manga": {
            "anilist": 53390,
            "shiki": 23390,
            "mangadex": "304ceac3-8cdb-4fe7-acf7-2b6ff7a60613",
        },
    },
    {
        "key": "steins-gate",
        "en": "Steins;Gate",
        "jp": "STEINS;GATE",
        "aliases": ["Steins;Gate"],
        "mal": 9253,
        "anilist": 9253,
        "manga": {
            "anilist": 47517,
            "shiki": 17517,
        },
    },
    {
        "key": "nge",
        "en": "Neon Genesis Evangelion",
        "jp": "新世紀エヴァンゲリオン",
        "aliases": ["Neon Genesis Evangelion", "Shin Seiki Evangelion", "Shinseiki Evangelion"],
        "mal": 30,
        "anilist": 30,
        "manga": {
            "anilist": 30698,
            "shiki": 698,
            "mangadex": "aaedcbda-ea61-4e7b-8143-7a475f327fbf",
        },
    },
    {
        "key": "spirited-away",
        "en": "Spirited Away",
        "jp": "千と千尋の神隠し",
        "aliases": ["Spirited Away", "Sen to Chihiro no Kamikakushi"],
        "mal": 199,
        "anilist": 199,
        "manga": {},
    },
    {
        "key": "one-punch-man",
        "en": "One Punch Man",
        "jp": "ワンパンマン",
        "aliases": ["One Punch Man"],
        "mal": 30276,
        "anilist": 30276,
        "manga": {
            "anilist": 74347,
            "shiki": 44347,
            "mangadex": "d8a959f7-648e-4c8d-8f23-f1f3f8e129f3",
        },
    },
    {
        "key": "your-name",
        "en": "Your Name",
        "jp": "君の名は。",
        "aliases": ["Your Name", "Kimi no Na wa"],
        "mal": 32281,
        "anilist": 32281,
        "manga": {
            "anilist": 97337,
            "shiki": 99314,
        },
    },
    {
        "key": "demon-slayer",
        "en": "Demon Slayer: Kimetsu no Yaiba",
        "jp": "鬼滅の刃",
        "aliases": ["Demon Slayer: Kimetsu no Yaiba", "Kimetsu no Yaiba"],
        "mal": 38000,
        "anilist": 38000,
        "manga": {
            "anilist": 87216,
            "shiki": 96792,
            "mangadex": "62040a44-0935-46b7-a691-5ae5833af0ae",
        },
    },
]

TITLE_BY_KEY = {t["key"]: t for t in TITLES}