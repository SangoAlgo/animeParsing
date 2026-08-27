import requests

def search_smotret(title):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    url = f"https://smotret-anime.online/api/series/?search={title}"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    items = data.get('data', [])
    if not items:
        return
        
    series_id = items[0]['id']
    print(f"Found {items[0]['title']} (ID: {series_id})")
    
    trans_url = f"https://smotret-anime.online/api/translations/?seriesId={series_id}"
    resp = requests.get(trans_url, headers=headers)
    if resp.status_code == 200:
        translations = resp.json().get('data', [])
        for t in translations:
            print(f"- {t.get('authorsList', ['Unknown'])[0]} (Type: {t.get('type')}) - Eps: {t.get('episodesCount')}")

if __name__ == '__main__':
    search_smotret('Brotherhood')
