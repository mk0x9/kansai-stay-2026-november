# Distance helpers: nearest Keihan Premium Car station for a point.
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
STATIONS = json.load(open(f"{HERE}/stations.json"))["stations"]


def meters(a_lat, a_lng, b_lat, b_lng):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b_lng - a_lng) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def nearest(lat, lng):
    return min(((meters(lat, lng, s["lat"], s["lng"]), s) for s in STATIONS), key=lambda t: t[0])
