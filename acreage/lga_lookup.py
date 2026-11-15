#!/usr/bin/env python3
"""Find the council (LGA) for blocks that don't have one, from their map point, using the ABS's free 2021
council boundaries (geo.abs.gov.au). Cached in lga-cache.json by rounded point; scan_acreage.py uses it."""
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
U = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/LGA/FeatureServer/0/query"
def key(la, lo): return f"{round(la, 3)},{round(lo, 3)}"
def main():
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: cache = json.load(open(P("lga-cache.json")))
    except Exception: cache = {}
    todo = {key(r["lat"], r["lng"]): (r["lat"], r["lng"]) for r in d["listings"] if not r.get("lga") and r.get("lat")}
    todo = {k: v for k, v in todo.items() if k not in cache}
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    print("LGA lookup: to do", len(todo))
    for i, (k, (la, lo)) in enumerate(list(todo.items())[:limit]):
        q = {"geometry": f"{lo},{la}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
             "outFields": "lga_name_2021,state_name_2021", "returnGeometry": "false", "f": "json"}
        for t in range(3):
            try:
                res = json.loads(urllib.request.urlopen(U + "?" + urllib.parse.urlencode(q), timeout=40).read()); break
            except Exception: res = None; time.sleep(3 * (t + 1))
        if res is None: continue
        f = res.get("features") or []
        cache[k] = f[0]["attributes"]["lga_name_2021"] if f else ""
        if i % 100 == 99: json.dump(cache, open(P("lga-cache.json"), "w")); print("  ", i + 1, flush=True)
        time.sleep(0.2)
    json.dump(cache, open(P("lga-cache.json"), "w"))
    print("LGA lookup: cached", len(cache))
if __name__ == "__main__":
    main()
