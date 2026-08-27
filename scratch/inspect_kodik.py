import sys
sys.path.insert(0, 'backend')

import re
import requests
from kodik import search_by_shikimori_id, HEADERS

results = search_by_shikimori_id(1735)
item = results[0]
seasons = item.get('seasons', {})
s1 = seasons.get('1', {})
eps = s1.get('episodes', {})
ep2_data = eps.get('2')
link_url = ep2_data if isinstance(ep2_data, str) else (ep2_data.get('link') if isinstance(ep2_data, dict) else item.get('link'))
if link_url.startswith('//'):
    link_url = 'https:' + link_url

print("Fetching Kodik iframe:", link_url)
page = requests.get(link_url, headers=HEADERS, timeout=10)
html = page.text

print("\n--- Searching for 'playerSettings' / 'skip' in HTML ---")
for m in re.finditer(r'(.{0,150}(?:playerSettings|skipObject|skipbutton|skip_time|skipTimes|opening|ending).{0,150})', html, re.I):
    print("Match:", m.group(1).strip())
    print("---")

print("\n--- Searching for all Javascript variable declarations in HTML ---")
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    print(f"\n--- Script #{i} (len: {len(s)}) ---")
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    for l in lines[:30]:
        print("  ", l[:120])
