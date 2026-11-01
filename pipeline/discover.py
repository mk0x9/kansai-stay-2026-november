# Discovery: every listing with a room for 2 adults on any night of Nov 19-21 (and the 3-night stay 19-22) in the
# Kyoto and central Osaka search areas. Run: browser-use < discover.py   -> data/candidates.json
import json, math, os, time
HERE = "/Users/mikhail/code/jalan-trip-2026-november/kansai-stay-2026-november/pipeline"
exec(open(f"{HERE}/jalan_lib.py").read())
AREAS = {
    "260000": {"pref": "Kyoto", "lrg": {"260500": "京都駅周辺", "260200": "河原町・烏丸・大宮周辺", "262300": "祇園・東山・北白川周辺",
                                        "262000": "嵯峨野・嵐山・高雄", "261400": "大原・鞍馬・貴船", "263300": "京都南部（宇治・長岡京・山崎）"}},
    "270000": {"pref": "Osaka", "lrg": {"272000": "大阪駅・梅田駅・福島・淀屋橋・本町", "272600": "大阪城・京橋・市内東部"}},
}
SEARCHES = {"19": (19, 1), "20": (20, 1), "21": (21, 1), "full": (19, 3)}
cands = json.load(open(f"{HERE}/data/candidates.json")) if os.path.exists(f"{HERE}/data/candidates.json") else {}
errors = []  # reruns merge into the existing file (Jalan sometimes returns an empty page)
tab = Tab()
try:
    tab.goto("https://www.jalan.net/")
    jobs = [(ken, lrg, tag) for ken, a in AREAS.items() for lrg in a["lrg"] for tag in SEARCHES]
    pending = [(j, 1) for j in jobs]
    counts = {}
    while pending:
        batch, pending = pending[:9], pending[9:]
        urls = [city_search_url(ken, lrg, *SEARCHES[tag], page=pg) for (ken, lrg, tag), pg in batch]
        for ((ken, lrg, tag), pg), res in zip(batch, parse_fetch(tab, urls, "searchlist", conc=3)):
            d = res.get("data") or {}
            if res.get("blocked") or res.get("status") != 200:
                errors.append(res["url"]); continue
            if pg == 1:
                counts[f"{lrg}/{tag}"] = d.get("count")
                if (d.get("count") or 0) > 30:
                    pending += [((ken, lrg, tag), p) for p in range(2, math.ceil(d["count"] / 30) + 1)]
            for it in d.get("items", []):
                if not it["yadNo"]:
                    continue
                c = cands.setdefault(it["yadNo"], {**it, "ken": ken, "pref": AREAS[ken]["pref"], "lrg": lrg,
                                                   "lrgName": AREAS[ken]["lrg"][lrg], "avail": []})
                if tag not in c["avail"]:
                    c["avail"].append(tag)
    json.dump(cands, open(f"{HERE}/data/candidates.json", "w"), ensure_ascii=False)
    print(json.dumps(counts))
    print("candidates", len(cands), "errors", len(errors), errors[:5])
finally:
    tab.close()
