import json

data = json.load(open("data/anime.json", encoding="utf-8"))
for t in data["titles"]:
    animan = t["sources"]["animan"]
    items = animan.get("episodes", {}).get("items", [])
    if items:
        print(f"=== {t.get('key')} ({len(items)} eps) ===")
        for ep in items[:3]:
            ts = ep.get("timestamps") or {}
            op = ts.get("op")
            ed = ts.get("ed")
            op_s = f"{op['start_fmt']} - {op['end_fmt']} ({op['start_s']}s -> {op['end_s']}s)" if op else "None"
            ed_s = f"{ed['start_fmt']} - {ed['end_fmt']} ({ed['start_s']}s -> {ed['end_s']}s)" if ed else "None"
            src = ts.get("source", "template")
            print(f"  Ep {ep['number']}: OP: {op_s} | ED: {ed_s} | {src}")
