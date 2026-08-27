import requests
import re
r = requests.get('https://smotret-anime.org/translations/embed/4082866', timeout=5)
print('video' in r.text, 'file' in r.text, 'url' in r.text)
matches = re.findall(r'(https://[^\'\"]+\.(?:m3u8|mp4)[^\'\"]*)', r.text)
print('Matches:', matches)
