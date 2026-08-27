import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

d = json.load(open("data/anime.json", encoding="utf-8"))
for t in d["titles"]:
    print("#" * 10, t["key"])
    j = (t["sources"].get("jikan_myanimelist", {}) or {}).get("data") or {}
    for r in j.get("relations", []) or []:
        entries = [
            f"{e.get('type')}:{e.get('mal_id')}:{e.get('name')}" for e in (r.get("entry") or [])
        ]
        print("  jikan rel:", r.get("relation"), entries[:3])
    al = t["sources"].get("anilist") or {}
    for e in (al.get("relations", {}).get("edges") or [])[:12]:
        n = e.get("node") or {}
        print(
            "  anilist rel:", e.get("relationType"), n.get("type"),
            n.get("id"), n.get("idMal"), (n.get("title") or {}).get("romaji"),
        )
    sh = t["sources"].get("shikimori", {}).get("related") or []
    for r in sh:
        m = r.get("manga")
        if m:
            print("  shiki rel:", r.get("relation"), "manga", m.get("id"), m.get("name"))
