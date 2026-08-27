import requests
import concurrent.futures
import os
import re

def fetch_and_test_proxies():
    print('Fetching SOCKS5 proxy list from ProxyScrape API...')
    try:
        resp = requests.get('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=5000&country=all&ssl=all&anonymity=all', timeout=10)
        proxies = resp.text.strip().split()
    except Exception as e:
        print(f"Error fetching proxies: {e}")
        proxies = []
    
    if not proxies:
        return None
        
    print(f'Got {len(proxies)} proxies. Testing against kodikapi.com...')
    
    def check_proxy(p):
        try:
            proxy_url = f'socks5h://{p}'
            r = requests.get('https://kodikapi.com/search?token=89fb36d07bb8a84db3031070e1764667&shikimori_id=20', proxies={'http': proxy_url, 'https': proxy_url}, timeout=5)
            if r.status_code == 200:
                return proxy_url
            return None
        except Exception:
            return None
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        for p in ex.map(check_proxy, proxies[:100]):
            if p:
                return p
    return None

def update_env(proxy_url):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"KODIK_PROXY={proxy_url}\n")
        print(f"Created .env with KODIK_PROXY={proxy_url}")
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'KODIK_PROXY=' in content:
        content = re.sub(r'KODIK_PROXY=[^\r\n]*', f'KODIK_PROXY={proxy_url}', content)
    else:
        content += f"\nKODIK_PROXY={proxy_url}\n"
        
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated .env with KODIK_PROXY={proxy_url}")

if __name__ == '__main__':
    proxy = fetch_and_test_proxies()
    if proxy:
        print(f"Found working proxy: {proxy}")
        update_env(proxy)
    else:
        print("Could not find a working proxy. Try again later.")
