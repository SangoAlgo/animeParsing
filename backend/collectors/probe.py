"""Quick connectivity probe for all sources. Run: python collectors/probe.py"""
import json
import ssl
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get(url, headers=None, timeout=25, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read()


def main():
    probes = [
        ("AniList", "https://graphql.anilist.co",
         {"Content-Type": "application/json", "Accept": "application/json"},
         b'{"query":"query($id:Int){Media(id:$id){id title{romaji english native}}}","variables":{"id":1}}'),
        ("Kitsu", "https://kitsu.app/api/edge/anime?filter[slug]=cowboy-bebop&page[limit]=1",
         {"Accept": "application/vnd.api+json"}, None),
        ("Shikimori", "https://shikimori.one/api/animes/302", {"User-Agent": "AnimeParsing/1.0"}, None),
        ("Jikan/MAL", "https://api.jikan.moe/v4/anime/1?sfw", None, None),
        ("AniDB HTML", "https://anidb.net/anime/1075", None, None),
        ("Bangumi", "https://api.bgm.tv/v0/subjects/857", {"User-Agent": "AnimeParsing/1.0"}, None),
        ("AnimeThemes", "https://api.animethemes.moe/anime?include=animethemes.animethemeentries.videos&filter[slug]=cowboy-bebop", None, None),
    ]
    for name, url, headers, body in probes:
        try:
            t0 = time.time()
            status, data = get(url, headers, data=body)
            preview = data[:160].decode("utf-8", "replace").replace("\n", " ")
            print(f"[OK]  {name:12s} {status} in {time.time()-t0:.1f}s | {preview}")
        except Exception as e:
            print(f"[ERR] {name:12s} {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()