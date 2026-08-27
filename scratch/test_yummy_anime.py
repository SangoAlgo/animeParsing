import asyncio
from anicli_api.source.yummy_anime import Extractor

async def main():
    ex = Extractor()
    print("Searching FMA Brotherhood...")
    res = ex.search("Brotherhood")
    for r in res:
        print(f"Cand: {r.title}")
        anime = r.get_anime()
        eps = anime.get_episodes()
        print(f"Eps count: {len(eps)}")
        if eps:
            sources = eps[0].get_sources()
            for s in sources:
                print(f"  Source: {s.title}")
                try:
                    for v in s.get_videos():
                        print(f"    Video: {v.quality} {v.type}")
                except Exception as e:
                    pass
        print("---")

if __name__ == "__main__":
    asyncio.run(main())
