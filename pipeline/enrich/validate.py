# Check an enrichment output file against its input. Usage: python3 validate.py <input.json> <output.json>
import json, sys

ENUMS = {
    "type": {"hotel", "ryokan", "guesthouse", "hostel", "apartment", "machiya"},
    "style": {"Western", "Japanese", "Japanese-Western"},
    "beds": {"twin", "double", "queen", "king", "triple", "futon", "bunk", "mixed", "unknown"},
    "bathroom": {"private", "shared", "unknown"},
    "smoking": {"non-smoking", "smoking", "unknown"},
    "breakfast": {"buffet", "set meal", "in-room", "none", "unknown"},
}
inp = json.load(open(sys.argv[1]))
try:
    out = json.load(open(sys.argv[2]))
except Exception as e:
    sys.exit(f"INVALID JSON: {e}")
problems = []
by_id = {str(o.get("yadNo")): o for o in out}
for p in inp:
    o = by_id.get(str(p["yadNo"]))
    if not o:
        problems.append(f"{p['yadNo']}: missing property"); continue
    if o.get("type") not in ENUMS["type"]:
        problems.append(f"{p['yadNo']}: bad type {o.get('type')!r}")
    if not o.get("name_en") or not o.get("strong_points"):
        problems.append(f"{p['yadNo']}: missing name_en or strong_points")
    for rc in p["rooms"]:
        r = (o.get("rooms") or {}).get(rc)
        if not r:
            problems.append(f"{p['yadNo']}: missing room {rc}"); continue
        for k in ("style", "beds", "bathroom", "smoking"):
            if r.get(k) not in ENUMS[k]:
                problems.append(f"{p['yadNo']} room {rc}: bad {k} {r.get(k)!r}")
    for pc in p["plans"]:
        q = (o.get("plans") or {}).get(pc)
        if not q:
            problems.append(f"{p['yadNo']}: missing plan {pc}"); continue
        if q.get("breakfast") not in ENUMS["breakfast"]:
            problems.append(f"{p['yadNo']} plan {pc}: bad breakfast {q.get('breakfast')!r}")
if problems:
    print("\n".join(problems[:40])); sys.exit(1)
print(f"ok {len(inp)} properties")
