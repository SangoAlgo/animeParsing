import urllib.request
import json

def test_api():
    # 1. Health
    with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as r:
        print("Healthcheck status:", r.status, r.read().decode())

    # 2. Titles query
    with urllib.request.urlopen("http://127.0.0.1:8000/api/titles?limit=3") as r:
        data = json.loads(r.read().decode())
        titles_list = data.get('titles') or data.get('items') or []
        print(f"Titles API: total = {data.get('total')}, returned = {len(titles_list)}")
        for item in titles_list:
            names = item.get('names', {})
            print(f"  - {item.get('key')}: {names.get('ru') or names.get('en')} ({item.get('sources', {}).get('animan', {}).get('facts', {}).get('year')})")

    # 3. Static HTML
    with urllib.request.urlopen("http://127.0.0.1:8000/") as r:
        html = r.read().decode()
        has_root = '<div id="root">' in html
        print(f"Frontend Static serving: status {r.status}, HTML bytes = {len(html)}, has root = {has_root}")

    # 4. Search query
    with urllib.request.urlopen("http://127.0.0.1:8000/api/titles?q=naruto&limit=2") as r:
        sdata = json.loads(r.read().decode())
        print(f"Search 'naruto': total found = {sdata.get('total')}")

if __name__ == "__main__":
    test_api()
