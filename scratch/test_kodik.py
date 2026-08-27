import requests

def search_kodik(title):
    # Common open token used by Kodik players
    token = '89fb36d07bb8a84db3031070e1764667'
    url = 'https://kodikapi.com/search'
    
    resp = requests.post(url, data={'token': token, 'title': title})
    if resp.status_code == 200:
        data = resp.json()
        print(f"Results for {title}: {len(data.get('results', []))}")
        
        studios = set()
        for res in data.get('results', []):
            studio = res.get('translation', {}).get('title')
            episodes = res.get('episodes_count', 0)
            if studio:
                studios.add(f"{studio} ({episodes} eps)")
        
        print("Studios found:")
        for s in studios:
            print(s)
    else:
        print(f"Failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    search_kodik("Steins;Gate")
