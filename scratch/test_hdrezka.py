from curl_cffi import requests
from bs4 import BeautifulSoup

def test_hdrezka(query):
    url = f"https://hdrezka-home.tv/search/?do=search&subaction=search&q={query}"
    resp = requests.get(url, impersonate="chrome")
    print("Status:", resp.status_code)
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.select('.b-content__inline_item-link a')
        print(f"Found {len(results)} links")
        for a in results:
            print(a.text.strip(), a['href'])

if __name__ == "__main__":
    test_hdrezka("Brotherhood")
