import requests
from bs4 import BeautifulSoup
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

r = requests.get('https://www.animefillerlist.com/shows', headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

shows = {}
for a in soup.select('div.Group a'):
    href = a.get('href', '')
    if '/shows/' in href:
        slug = href.split('/shows/')[-1].strip('/')
        shows[slug] = a.text.strip()

print(f"Total shows available on AnimeFillerList: {len(shows)}")
print("Sample shows:", list(shows.items())[:20])

with open('data/filler_shows_index.json', 'w', encoding='utf-8') as f:
    json.dump(shows, f, ensure_ascii=False, indent=2)
