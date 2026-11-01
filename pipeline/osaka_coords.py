# Coordinates for Osaka candidates (Jalan detail page static-map center), to keep those near Keihan Premium Car stations.
import json, re, math
HERE = "/Users/mikhail/code/jalan-trip-2026-november/kansai-stay-2026-november/pipeline"
exec(open(f"{HERE}/jalan_lib.py").read())
cands = json.load(open(f"{HERE}/data/candidates.json"))
path = f"{HERE}/data/coords.json"
coords = json.load(open(path)) if os.path.exists(path) else {}
import os
todo = [y for y, c in cands.items() if c["pref"] == "Osaka" and coords.get(y) is None]
CENTER = re.compile(r"center=(-?[\d.]+)(?:,|%2C)(-?[\d.]+)")
tab = Tab()
try:
    tab.goto("https://www.jalan.net/")
    for b in range(0, len(todo), 40):
        batch = todo[b:b + 40]
        res = fetch_many(tab, [f"https://www.jalan.net/yad{i}/" for i in batch], 4)
        for i, r in zip(batch, res):
            html = r.get("html") or ""
            if r.get("status") != 200 or re.search(r"エラー画面|アクセスが集中", html[:3000]):
                continue
            m = CENTER.search(html)
            coords[i] = [float(m.group(1)), float(m.group(2))] if m else None
        json.dump(coords, open(path, "w"))
        print("batch", b // 40, "total", len(coords))
finally:
    tab.close()
