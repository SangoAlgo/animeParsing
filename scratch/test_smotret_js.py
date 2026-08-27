import requests
import re
resp = requests.get('https://smotret-anime.org/js/app/embed.min.js', headers={'User-Agent': 'Mozilla/5.0'})
if resp.status_code == 200:
    print('Length:', len(resp.text))
    urls = re.findall(r'url\s*:\s*[\'"](.*?)[\'"]', resp.text)
    print(list(set(urls))[:20])
