import requests
import re
resp = requests.get('https://smotret-anime.org/translations/embed/5526677', headers={'User-Agent': 'Mozilla/5.0'})
links = re.findall(r'https?://[^\s\"\']+', resp.text)
kodik_links = [l for l in links if 'kodik.info' in l or 'mp4' in l or 'm3u8' in l or 'video' in l]
print(kodik_links)
