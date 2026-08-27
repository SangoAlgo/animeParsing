import re
with open('animego.html', 'r', encoding='utf-8') as f:
    text = f.read()
import urllib.parse
for match in re.findall(r'href=[\"\'](https://animego\.org/anime/[^\"\']+)[\"\'][^>]*title=[\"\']([^\"\']+)[\"\']', text):
    print(match)
