import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from parsers.episodes import parse_anilibria, parse_animevost
from collectors.titles import TITLES

RU_NAMES = {
    'cowboy-bebop': 'Ковбой Бибоп',
    'death-note': 'Тетрадь смерти',
    'fma-brotherhood': 'Стальной алхимик: Братство',
    'steins-gate': 'Врата Штейна',
    'attack-on-titan': 'Атака титанов',
    'nge': 'Евангелион нового поколения',
    'spirited-away': 'Унесённые призраками',
    'your-name': 'Твоё имя',
    'one-punch-man': 'Ванпанчмен',
    'demon-slayer': 'Истребитель демонов',
}

YEAR_MAP = {
    'cowboy-bebop': 1998,
    'death-note': 2006,
    'fma-brotherhood': 2009,
    'steins-gate': 2011,
    'attack-on-titan': 2013,
    'nge': 1995,
    'spirited-away': 2001,
    'your-name': 2016,
    'one-punch-man': 2015,
    'demon-slayer': 2019,
}

EPS_MAP = {
    'cowboy-bebop': 26,
    'death-note': 37,
    'fma-brotherhood': 64,
    'steins-gate': 24,
    'attack-on-titan': 25,
    'nge': 26,
    'spirited-away': 1,
    'your-name': 1,
    'one-punch-man': 12,
    'demon-slayer': 26,
}

for t in TITLES:
    meta = {
        'key': t['key'],
        'title_ru': RU_NAMES.get(t['key'], t['en']),
        'title_en': t['en'],
        'year': YEAR_MAP.get(t['key'], 2010),
        'episodes_total': EPS_MAP.get(t['key'], 24),
        'format': 'MOVIE' if EPS_MAP.get(t['key']) == 1 else 'TV',
    }
    al_res = parse_anilibria(meta)
    av_res = parse_animevost(meta)
    print(f"=== {t['key']} ({meta['title_ru']}) [Expected: {meta['episodes_total']} eps] ===")
    if al_res:
        print(f"  AniLibria: '{al_res.get('matched_title')}' -> {al_res.get('episodes_count')} eps")
    else:
        print("  AniLibria: None")
    if av_res:
        print(f"  AnimeVost: '{av_res.get('matched_title')}' -> {av_res.get('episodes_count')} eps")
    else:
        print("  AnimeVost: None")
