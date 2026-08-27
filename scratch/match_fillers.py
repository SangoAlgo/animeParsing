import sqlite3
import json
import re

# Load AnimeFillerList index
with open('data/filler_shows_index.json', 'r', encoding='utf-8') as f:
    filler_shows = json.load(f)

# Connect to anime.db
conn = sqlite3.connect('data/anime.db')
c = conn.cursor()
c.execute("SELECT key, title_ru, title_en, episodes_total, mal_id FROM titles")
db_titles = c.fetchall()

def normalize_title(t):
    if not t: return ""
    t = t.lower()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    return ' '.join(t.split())

matched = {}
unmatched = []

# Build lookup by normalized English name
slug_by_norm = {}
for slug, show_name in filler_shows.items():
    slug_by_norm[normalize_title(show_name)] = slug
    slug_by_norm[normalize_title(slug.replace('-', ' '))] = slug

# Specific manual alias map for top franchises
ALIASES = {
    'naruto': 'naruto',
    'naruto-shippuuden': 'naruto-shippuden',
    'bleach': 'bleach',
    'one-piece': 'one-piece',
    'boruto-naruto-next-generations': 'boruto-naruto-next-generations',
    'black-clover': 'black-clover',
    'fairy-tail': 'fairy-tail',
    'fairy-tail-2014': 'fairy-tail',
    'dragon-ball': 'dragon-ball',
    'dragon-ball-z': 'dragon-ball-z',
    'dragon-ball-super': 'dragon-ball-super',
    'hunter-x-hunter-2011': 'hunter-x-hunter-2011',
    'hunter-x-hunter': 'hunter-x-hunter',
    'gintama': 'gintama',
    'detective-conan': 'detective-conan',
    'boku-no-hero-academia': 'my-hero-academia',
    'boku-no-hero-academia-2nd-season': 'my-hero-academia',
    'shingeki-no-kyojin': 'attack-titan',
    'death-note': 'death-note',
    'jujutsu-kaisen': 'jujutsu-kaisen',
    'kimetsu-no-yaiba': 'demon-slayer-kimetsu-no-yaiba',
    'tokyo-ghoul': 'tokyo-ghoul',
    'fullmetal-alchemist': 'fullmetal-alchemist',
    'fullmetal-alchemist-brotherhood': 'fullmetal-alchemist-brotherhood',
    'rurouni-kenshin': 'rurouni-kenshin',
    'inuyasha': 'inuyasha',
    'sailor-moon': 'sailor-moon',
    'soul-eater': 'soul-eater',
    'yu-gi-oh': 'yu-gi-oh',
    'pokemon': 'pokemon',
    'katekyo-hitman-reborn': 'katekyo-hitman-reborn',
    'dgray-man': 'd-gray-man',
    'blue-exorcist': 'blue-exorcist-ao-no-exorcist',
    'seven-deadly-sins': 'seven-deadly-sins',
    'nanatsu-no-taizai': 'seven-deadly-sins',
}

for key, t_ru, t_en, ep_total, mal_id in db_titles:
    if key in ALIASES:
        matched[key] = (ALIASES[key], t_ru, t_en, ep_total)
        continue
    
    norm_en = normalize_title(t_en)
    if norm_en in slug_by_norm:
        matched[key] = (slug_by_norm[norm_en], t_ru, t_en, ep_total)
        continue
        
    norm_key = normalize_title(key.replace('-', ' '))
    if norm_key in slug_by_norm:
        matched[key] = (slug_by_norm[norm_key], t_ru, t_en, ep_total)
        continue
        
    unmatched.append((key, t_ru, t_en, ep_total))

print(f"Matched {len(matched)} titles to AnimeFillerList!")
print(f"Sample matched: {list(matched.items())[:15]}")
