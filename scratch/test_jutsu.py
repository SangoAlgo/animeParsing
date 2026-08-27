import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

query = urllib.parse.quote_plus('Стальной алхимик')
resp = requests.post('https://jut.su/search', data={'word': query})
soup = BeautifulSoup(resp.text, 'html.parser')
url = soup.select_one('.header_video a')['href']
url = 'https://jut.su' + url
print('Found:', url)

ep_page = requests.get(url + 'episode-1.html')
print(ep_page.status_code)
links = re.findall(r'https?://[^\s\"\']+\.mp4', ep_page.text)
print(list(set(links)))
