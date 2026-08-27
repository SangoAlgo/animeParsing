import asyncio
from anicli_api.source.animego import Extractor

def main():
    ex = Extractor()
    print("Searching FMA Brotherhood...")
    res = ex.search("Fullmetal Alchemist Brotherhood")
    for r in res:
        print(f"Cand: {r.title} ({r.url})")
        anime = r.get_anime()
        eps = anime.get_episodes()
        print(f"Eps count: {len(eps)}")
        if len(eps) > 0:
            sources = eps[0].get_sources()
            for s in sources:
                print(f"  Source: {s.title}")

if __name__ == "__main__":
    main()
