# Build ../data.js (window.STAYS, window.STATIONS) from data/prepped.json + enrich/out/K_*.json.
# Run: python3 build_data.py   (works before enrichment too, falling back to the Japanese text)
import glob, json, os, re
from geo import STATIONS, nearest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG_BASE = "https://cdn.jalan.jp/jalan/images/"
MEALS_EN = {"朝・夕": "Breakfast & dinner", "朝のみ": "Breakfast only", "夕のみ": "Dinner only", "食事なし": "Room only"}
AREA_EN = {"260500": "Kyoto Station", "260200": "Kawaramachi · Karasuma · Omiya", "262300": "Gion · Higashiyama · Kitashirakawa",
           "262000": "Arashiyama · Sagano · Takao", "261400": "Ohara · Kurama · Kibune", "263300": "Southern Kyoto (Uji, Nagaokakyo)",
           "272000": "Umeda · Yodoyabashi · Honmachi", "272600": "Osaka Castle · Kyobashi"}
SKIP = {"", "unknown", None}


def img(u):
    if not u:
        return None
    return u[len(IMG_BASE):] if u.startswith(IMG_BASE) else u


def trim(v, n=300):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return v if len(v) <= n else v[:n - 1].rstrip() + "…"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compact(d):
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def cancel_until(text):
    m = re.search(r"キャンセル料無料.{0,3}(\d{4})年(\d{1,2})月(\d{1,2})日", text or "")
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None


def public_bath(q):
    """Large shared bath: Jalan lists men's or women's indoor/outdoor baths."""
    counts = [c for k in ("indoor_mfx", "rotenburo_mfx") for c in (q.get(k) or [])[:2]]
    return 1 if any(counts) else 0


SHARED_EVIDENCE = re.compile(r"共同|共用|大浴場|トイレ|シャワー|バス|風呂|浴室")


def bathroom(room, r):
    """Jalan's "※バスなしトイレなし" facility tag alone (empty room text) is often a placeholder: KIORI suites carry it.
    Keep "shared" only when the room name or description itself talks about the bath or toilet."""
    v = room.get("bathroom")
    if v == "shared" and not SHARED_EVIDENCE.search((r.get("roomFullName") or "") + (r.get("roomName") or "") + (r.get("roomDetail") or "")):
        return None
    return v if v not in SKIP else None


def load_enrich():
    out = {}
    for f in sorted(glob.glob(f"{HERE}/enrich/out/K_*.json")):
        for e in json.load(open(f)):
            out[str(e["yadNo"])] = e
    return out


def main():
    props = json.load(open(f"{HERE}/data/prepped.json"))
    enrich = load_enrich()
    extra = json.load(open(f"{HERE}/data/coords.json")) if os.path.exists(f"{HERE}/data/coords.json") else {}
    stays, missing = [], []
    for q in props:
        y = str(q["yadNo"])
        e = enrich.get(y)
        if not e:
            missing.append(y); e = {}
        c = q.get("coords") or extra.get(y)
        d, s = nearest(*c) if c else (None, None)
        plans = []
        for r in q["plans"]:
            room = (e.get("rooms") or {}).get(r["roomTypeCd"], {})
            pl = (e.get("plans") or {}).get(r["planCd"], {})
            ri = (r.get("roomImages") or [[None]])[0][0] if r.get("roomImages") else None
            n = r["nightly"]
            plans.append(compact({
                "name": trim(pl.get("plan_name_en") or r.get("planName"), 140), "meals": MEALS_EN.get(r["meal"], r["meal"]),
                "bf": pl.get("breakfast") if pl.get("breakfast") not in SKIP else None,
                "room": trim(room.get("room_en") or r.get("roomFullName") or r.get("roomName"), 140),
                "style": room.get("style"), "beds": room.get("beds") if room.get("beds") not in SKIP else None,
                "size": room.get("size"), "view": room.get("view") if room.get("view") not in ("none",) else None,
                "bathroom": bathroom(room, r),
                "smoking": room.get("smoking") if room.get("smoking") not in SKIP else None,
                "photo": img(ri), "prices": [n.get("19"), n.get("20"), n.get("21")],
                "cancel": cancel_until(r.get("cancel")), "oneNight": True if r.get("maxOneNight") else None,
                "planCd": r["planCd"], "roomCd": r["roomTypeCd"],
            }))
        photos = compact({k: img(v) for k, v in (q.get("images") or {}).items()})
        stays.append(compact({
            "id": y, "name": e.get("name_en") or q["name"], "nameJp": q["name"], "city": q["pref"],
            "type": e.get("type") or "hotel", "area": AREA_EN.get(q["lrg"], q["area"]), "areaJp": q["area"],
            "lat": c[0] if c else None, "lng": c[1] if c else None,
            "stn": s["name"] if s else None, "stnM": int(round(d, -1)) if d is not None else None,
            "photos": photos,
            "rating": num(q.get("rating")), "reviews": q.get("reviews"),
            "scores": compact({k: num(q.get(h)) for k, h in [("room", "r_room"), ("bath", "r_bath"), ("breakfast", "r_breakfast"),
                                                              ("dinner", "r_dinner"), ("service", "r_service"), ("clean", "r_clean")]}),
            "loc": trim(e.get("location_en"), 200), "access": trim(q.get("access"), 220),
            "strong": [trim(x, 180) for x in e.get("strong_points") or []], "watch": trim(e.get("watch_outs"), 220),
            "summary": trim(e.get("review_summary_en"), 260), "bath": trim(e.get("public_bath_en"), 160), "pub": public_bath(q),
            "checkInOut": " / ".join(x.replace("\xa0", " ").strip() for x in (q.get("checkin"), q.get("checkout")) if x) or None,
            "plans": plans,
        }))
    js = ("// Generated by pipeline/build_data.py; do not edit.\n"
          f"window.IMG_BASE = {json.dumps(IMG_BASE)};\n"
          "window.STATIONS = " + json.dumps(STATIONS, ensure_ascii=False, separators=(",", ":")) + ";\n"
          "window.STAYS = " + json.dumps(stays, ensure_ascii=False, separators=(",", ":")) + ";\n")
    open(f"{ROOT}/data.js", "w").write(js)
    full = sum(1 for x in stays if any(all(v is not None for v in p["prices"]) for p in x["plans"]))
    print(json.dumps({"stays": len(stays), "kyoto": sum(x["city"] == "Kyoto" for x in stays), "osaka": sum(x["city"] == "Osaka" for x in stays),
                      "all_3_nights": full, "plans": sum(len(x["plans"]) for x in stays), "no_coords": [x["id"] for x in stays if "lat" not in x],
                      "missing_enrichment": len(missing), "bytes": len(js.encode())}))


if __name__ == "__main__":
    main()
