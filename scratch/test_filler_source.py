import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

def fetch_animefillerlist(show_slug: str):
    url = f"https://www.animefillerlist.com/shows/{show_slug}"
    print(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"Failed with status: {r.status_code}")
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. Check description / filler stats
        desc = soup.select_one('div.description')
        if desc:
            print("Description stats:", desc.text.strip().replace('\n', ' ')[:200])
            
        # 2. Check table of episodes
        table = soup.select_one('table.EpisodeList')
        if not table:
            print("No table.EpisodeList found")
            return None
            
        episodes = {}
        for tr in table.select('tbody tr'):
            td_num = tr.select_one('td.Number')
            td_title = tr.select_one('td.Title')
            td_type = tr.select_one('td.Type')
            td_date = tr.select_one('td.Date')
            
            if td_num and td_type:
                try:
                    num = int(td_num.text.strip())
                except:
                    continue
                type_raw = td_type.text.strip().lower()
                title_text = td_title.text.strip() if td_title else f"Episode {num}"
                
                # Normalize types:
                # 'manga canon' -> 'canon', 'anime canon' -> 'anime_canon', 'mixed canon/filler' -> 'mixed', 'filler' -> 'filler'
                if 'manga canon' in type_raw:
                    f_type = 'canon'
                    f_label = 'Канон манги'
                elif 'anime canon' in type_raw:
                    f_type = 'anime_canon'
                    f_label = 'Аниме-канон'
                elif 'mixed' in type_raw:
                    f_type = 'mixed'
                    f_label = 'Смешанный канон'
                elif 'filler' in type_raw:
                    f_type = 'filler'
                    f_label = 'Филлер'
                else:
                    f_type = 'canon'
                    f_label = 'Канон'
                    
                episodes[num] = {
                    "number": num,
                    "title_en": title_text,
                    "filler_type": f_type,
                    "filler_label": f_label,
                    "air_date": td_date.text.strip() if td_date else None,
                }
        print(f"Extracted {len(episodes)} episodes for '{show_slug}'")
        return episodes
    except Exception as e:
        print(f"Error fetching {show_slug}: {e}")
        return None

# Test on Naruto Shippuden, Bleach, One Piece, Jujutsu Kaisen
for slug in ['naruto-shippuden', 'naruto', 'bleach', 'one-piece']:
    res = fetch_animefillerlist(slug)
    if res:
        sample_fillers = [v for v in res.values() if v['filler_type'] == 'filler'][:3]
        sample_canon = [v for v in res.values() if v['filler_type'] == 'canon'][:3]
        print(f"   Sample Canon: {sample_canon}")
        print(f"   Sample Fillers: {sample_fillers}")
