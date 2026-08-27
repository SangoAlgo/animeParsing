import sys
sys.path.insert(0, 'backend')

import re
import requests
from kodik import search_by_shikimori_id, HEADERS


def parse_kodik_skip_button_str(skip_str: str) -> list[dict]:
    """Parses Kodik's skipButton string (e.g. '1:43-3:13,21:09-23:20')."""
    if not skip_str:
        return []
    
    def time_to_sec(t_str: str) -> float:
        parts = t_str.strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(parts[0])
    
    skips = []
    # format: "1:43-3:13,21:09-23:20" or "01:30-03:00"
    for idx, segment in enumerate(skip_str.split(',')):
        seg = segment.strip()
        if '-' in seg:
            p = seg.split('-')
            try:
                start_s = time_to_sec(p[0])
                end_s = time_to_sec(p[1])
                sk_type = "op" if idx == 0 else "ed"
                skips.append({
                    "start": start_s,
                    "end": end_s,
                    "type": sk_type,
                })
            except Exception:
                pass
    return skips


def extract_skips_from_kodik_html(html: str) -> list[dict]:
    # Match: parseSkipButton("1:43-3:13,21:09-23:20", "anime")
    m = re.search(r'parseSkipButton\s*\(\s*["\']([^"\']+)["\']', html)
    if m:
        return parse_kodik_skip_button_str(m.group(1))
    
    # Match: playerSettings.skipButton = "..."
    m2 = re.search(r'playerSettings\.skipButton\s*=\s*["\']([^"\']+)["\']', html)
    if m2:
        return parse_kodik_skip_button_str(m2.group(1))
        
    return []


# Test titles across Kodik
test_shiki_ids = [
    (1735, "Naruto Shippuden", 2),
    (1735, "Naruto Shippuden", 10),
    (40748, "Jujutsu Kaisen", 1),
    (40748, "Jujutsu Kaisen", 5),
    (44511, "Chainsaw Man", 1),
    (44511, "Chainsaw Man", 3),
    (1535, "Death Note", 1),
    (269, "Bleach", 1),
]

print("=== Testing 100% Kodik SkipButton HTML Parser ===")
for shiki_id, name, ep_num in test_shiki_ids:
    items = search_by_shikimori_id(shiki_id)
    if not items:
        print(f"[{name}] No Kodik items found")
        continue
    item = items[0]
    seasons = item.get('seasons', {})
    s1 = seasons.get('1', {})
    eps = s1.get('episodes', {})
    ep_data = eps.get(str(ep_num))
    link_url = ep_data if isinstance(ep_data, str) else (ep_data.get('link') if isinstance(ep_data, dict) else item.get('link'))
    if link_url:
        if link_url.startswith('//'):
            link_url = 'https:' + link_url
        page = requests.get(link_url, headers=HEADERS, timeout=8)
        skips = extract_skips_from_kodik_html(page.text)
        print(f"[{name} - Ep {ep_num}] -> Skips: {skips}")
