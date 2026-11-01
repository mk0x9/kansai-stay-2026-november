# Post-process scraped properties: best rows, image picks, compact enrichment inputs.
# Run: python3 prep.py   -> data/prepped.json, enrich/in/K_NN.json
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
NIGHTS = ["19", "20", "21"]
BATCH = int(os.environ.get("BATCH", "20"))
IMG_RULES = [
    ("room", r"客室|部屋|和室|洋室|和洋室|ベッド|スイート|ツイン|ダブル|ルーム"),
    ("bath", r"風呂|露天|湯船|大浴場|浴場|温泉|スパ|サウナ|バス"),
    ("food", r"朝食|夕食|料理|会席|膳|懐石|お食事|ディナー|ビュッフェ|レストラン"),
]


def cut(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def pick_images(p):
    caps = [(u, a or "") for u, a in p.get("image_captions") or []]
    seen, picks = set(), {}
    if p.get("images"):
        picks["main"] = p["images"][0]; seen.add(p["images"][0])
    for kind, rx in IMG_RULES:
        for u, a in caps:
            if u not in seen and re.search(rx, a):
                picks[kind] = u; seen.add(u); break
    return picks


def prep_property(p):
    s = p["search"]
    rows = []
    for r in p["plans"]:
        n = {str(k): v for k, v in (r.get("nightly") or {}).items() if v}
        if not n:
            continue
        full = round(sum(n.values()) / 3) if len(n) == 3 else None
        rows.append({**r, "nightly": n, "fullAvg": full, "minNight": min(n.values()),
                     "maxOneNight": bool(re.search(r"最大1泊", r.get("maxNightsNote") or ""))})
    rows.sort(key=lambda r: (r["fullAvg"] or 9e9, r["minNight"]))
    return {
        "yadNo": p["yadNo"], "name": s["name"].split("◆")[0].strip(), "pref": s["pref"], "lrg": s["lrg"],
        "area": s.get("lrgName"), "avail": s["avail"], "coords": p.get("coords"),
        "url": p["url"], "address": p.get("address"), "access": s.get("access"), "catch": s.get("catch"),
        "rating": p.get("rating") or s.get("rating"), "reviews": p.get("reviews") or s.get("reviews"),
        **{k: p.get(k) for k in ["r_room", "r_bath", "r_breakfast", "r_dinner", "r_service", "r_clean",
                                 "highly_rated", "review_highlight", "pr_text", "onsen", "private_bath", "rotenburo_mfx",
                                 "indoor_mfx", "sauna_mfx", "bath_notes", "rooms", "checkin", "checkout", "parking",
                                 "facilities", "services"]},
        "thumbs": s.get("thumbs"), "images": pick_images(p), "plans": rows,
    }


def enrich_input(q):
    rooms, plans = {}, {}
    for r in q["plans"]:
        rooms.setdefault(r["roomTypeCd"], {"name": cut(r.get("roomFullName") or r.get("roomName"), 110),
                                           "style_label": r.get("roomStyle"), "labels": r.get("roomLabels"),
                                           "facilities": cut(r.get("roomFacilities"), 100),
                                           "detail": cut(r.get("roomDetail"), 300)})
        has_meal = r.get("meal") not in ("食事なし", None)
        plans.setdefault(r["planCd"], {"name": cut(r.get("planName"), 120), "meal": r.get("meal"),
                                       "meal_detail": cut(r.get("mealDetail"), 80),
                                       "detail": cut(r.get("planDetail"), 260 if has_meal else 140)})
    return {
        "yadNo": q["yadNo"], "name": q["name"], "pref": q["pref"], "area": q["area"], "address": q["address"],
        "access": cut(q["access"], 180), "catch": q["catch"], "pr_text": cut(q["pr_text"], 260),
        "onsen": q["onsen"],
        "public_baths": {"outdoor_m_f_mixed": q["rotenburo_mfx"], "indoor_m_f_mixed": q["indoor_mfx"], "sauna_m_f_mixed": q["sauna_mfx"]},
        "rooms_count": q["rooms"], "rating": q["rating"], "highly_rated": q["highly_rated"],
        "review_highlight": cut(q["review_highlight"], 220), "facilities": cut(q["facilities"], 140),
        "rooms": rooms, "plans": plans,
    }


def main():
    props = [json.load(open(f)) for f in sorted(glob.glob(f"{HERE}/data/props/*.json"))]
    kept = [q for q in (prep_property(p) for p in props) if q["plans"]]
    json.dump(kept, open(f"{HERE}/data/prepped.json", "w"), ensure_ascii=False)
    for f in glob.glob(f"{HERE}/enrich/in/K_*.json"):
        os.remove(f)
    inputs = [enrich_input(q) for q in kept]
    for i in range(0, len(inputs), BATCH):
        json.dump(inputs[i:i + BATCH], open(f"{HERE}/enrich/in/K_{i // BATCH:02d}.json", "w"), ensure_ascii=False)
    print(f"scraped={len(props)} with_plans={len(kept)} rows={sum(len(q['plans']) for q in kept)} "
          f"rooms={sum(len(x['rooms']) for x in inputs)} plans={sum(len(x['plans']) for x in inputs)} "
          f"batches={(len(inputs) + BATCH - 1) // BATCH} chars={sum(len(json.dumps(x, ensure_ascii=False)) for x in inputs)}")


if __name__ == "__main__":
    main()
