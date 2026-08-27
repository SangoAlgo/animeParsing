import json
import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

mal_ids = [
    ("cowboy-bebop", 1, 26),
    ("death-note", 1535, 37),
    ("fma-brotherhood", 5114, 64),
    ("attack-on-titan", 16498, 25),
    ("steins-gate", 9253, 24),
    ("nge", 30, 26),
    ("one-punch-man", 30276, 12),
    ("demon-slayer", 38000, 26),
]

for key, mal_id, ep_count in mal_ids[:3]:
    print(f"=== Testing AniSkip for {key} (MAL ID: {mal_id}) ===")
    for ep in [1, 2, 5]:
        url = f"https://api.aniskip.com/v2/skip-times/{mal_id}/{ep}?types[]=op&types[]=ed&types[]=recap&types[]=mixed-op&types[]=mixed-ed&episodeLength=0"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Animan/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                data = json.load(resp)
                if data.get("found"):
                    results = data.get("results", [])
                    print(f"  Ep {ep}: Found {len(results)} timestamps")
                    for r in results:
                        st = r["interval"]["startTime"]
                        et = r["interval"]["endTime"]
                        print(f"    {r['skipType'].upper()}: {st:.2f}s ({int(st//60):02d}:{st%60:05.2f}) -> {et:.2f}s ({int(et//60):02d}:{et%60:05.2f})")
                else:
                    print(f"  Ep {ep}: not found")
        except Exception as e:
            print(f"  Ep {ep} Error: {e}")
