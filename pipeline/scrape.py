# Per-property scrape. Run: SHARD=0/8 browser-use < scrape.py   (LIMIT=n for a smoke test). Resumable.
# Scope: every Kyoto candidate; Osaka candidates within OSAKA_MAX_M of a Keihan Premium Car station
# (or without coordinates but with a Keihan station in the access text).
import json, os, re, time
HERE = "/Users/mikhail/code/jalan-trip-2026-november/kansai-stay-2026-november/pipeline"
exec(open(f"{HERE}/jalan_lib.py").read())
exec(open(f"{HERE}/geo.py").read().replace("os.path.dirname(os.path.abspath(__file__))", repr(HERE)))
OSAKA_MAX_M = 1000
LIMIT = int(os.environ.get("LIMIT", "0"))
SHARD, NSHARDS = map(int, os.environ.get("SHARD", "0/1").split("/"))
cands = json.load(open(f"{HERE}/data/candidates.json"))
coords = json.load(open(f"{HERE}/data/coords.json"))
os.makedirs(f"{HERE}/data/props", exist_ok=True)
logf = open(f"{HERE}/data/progress_{SHARD}.log", "a")


def log(msg):
    logf.write(time.strftime("%H:%M:%S ") + msg + "\n"); logf.flush()


def in_scope(y, c):
    if c["pref"] == "Kyoto":
        return True
    x = coords.get(y)
    if x:
        return nearest(*x)[0] <= OSAKA_MAX_M
    return bool(re.search(r"京阪|淀屋橋|北浜|天満橋", c.get("access") or ""))


todo = sorted(y for y, c in cands.items() if in_scope(y, c))
if SHARD == 0:
    json.dump(todo, open(f"{HERE}/data/scope.json", "w"))
log(f"in scope: {len(todo)} of {len(cands)}")
todo = todo[SHARD::NSHARDS]
if LIMIT:
    todo = todo[:LIMIT]
tab = Tab()
try:
    tab.goto("https://www.jalan.net/")
    streak = 0
    for i, y in enumerate(todo):
        path = f"{HERE}/data/props/{y}.json"
        if os.path.exists(path):
            continue
        for attempt in range(3):
            try:
                t0 = time.time()
                p = scrape_property(tab, y)
                if p["blocked"]:
                    raise RuntimeError("blocked")
                if not p.get("coords") or not p.get("rating"):  # page not fully rendered: take coords from raw HTML
                    h = (fetch_many(tab, [f"https://www.jalan.net/yad{y}/"], 1)[0].get("html") or "")
                    m = re.search(r"center=(-?[\d.]+)(?:,|%2C)(-?[\d.]+)", h)
                    if m and not p.get("coords"):
                        p["coords"] = [float(m.group(1)), float(m.group(2))]
                p["search"] = cands[y]
                json.dump(p, open(path, "w"), ensure_ascii=False)
                log(f"[{i+1}/{len(todo)}] {y} rows={len(p['plans'])}/{p['rowsTotal']} fetches={p['fetches']} {time.time()-t0:.1f}s")
                streak = 0
                break
            except Exception as e:
                streak += 1
                log(f"[{i+1}/{len(todo)}] {y} attempt {attempt+1} failed: {str(e)[:200]}")
                time.sleep(20 * (attempt + 1))
        if streak >= 6:
            log("too many consecutive failures, stopping"); break
    log("DONE")
finally:
    tab.close()
