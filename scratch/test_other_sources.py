import asyncio
import logging

logging.basicConfig(level=logging.ERROR)

async def test_extractor(name, module):
    try:
        ex = module.Extractor()
        res = ex.search("Brotherhood")
        if res:
            print(f"[{name}] SUCCESS: Found {len(res)} results")
        else:
            print(f"[{name}] SUCCESS (Empty): No results")
    except Exception as e:
        print(f"[{name}] FAILED: {e}")

async def main():
    try:
        from anicli_api.source import yummy_anime
        await test_extractor("yummy_anime", yummy_anime)
    except Exception as e: print("Failed to import yummy_anime:", e)
    
    try:
        from anicli_api.source import dreamcast
        await test_extractor("dreamcast", dreamcast)
    except Exception as e: print("Failed to import dreamcast:", e)

    try:
        from anicli_api.source import sameband
        await test_extractor("sameband", sameband)
    except Exception as e: print("Failed to import sameband:", e)

    try:
        from anicli_api.source import anilibme
        await test_extractor("anilibme", anilibme)
    except Exception as e: print("Failed to import anilibme:", e)

if __name__ == "__main__":
    asyncio.run(main())
