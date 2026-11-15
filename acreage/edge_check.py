#!/usr/bin/env python3
"""Town-edge check for NSW and VIC blocks (free state zoning map services, cached in edge-cache.json):
which zones lie within 2 km of the block. Flags: land zoned for houses nearby (the edge of town, where
rezoning happens next) and, in Victoria, the Urban Growth Zone (land set aside for future suburbs).
growth.py turns these into "growth path" signs."""
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
SVC = {"NSW": ("https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/Planning_Portal_Principal_Planning/MapServer/19/query", "SYM_CODE"),
       "VIC": ("https://plan-gis.mapshare.vic.gov.au/arcgis/rest/services/Planning/Vicplan_PlanningSchemeZones/MapServer/0/query", "ZONE_CODE")}
RES = {"NSW": ("R1", "R2", "R3", "R4"), "VIC": ("GRZ", "NRZ", "RGZ", "MUZ", "TZ")}

def get(url, q):
    for t in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "acreage-finder"}), timeout=25).read())
            if "error" not in d: return d
        except Exception: pass
        time.sleep(3 * (t + 1))
    return None

def main():
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: cache = json.load(open(P("edge-cache.json")))
    except Exception: cache = {}
    todo = sorted([r for r in d["listings"] if r["s"] in SVC and r.get("lat") and not r.get("uo") and str(r["id"]) not in cache], key=lambda r: r["s"] != "VIC")   # VIC first: its service is quicker
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    print("Town-edge check: to do", len(todo), "| doing up to", limit)
    from concurrent.futures import ThreadPoolExecutor
    def one(r):
        url, fld = SVC[r["s"]]
        res = get(url, {"geometry": f"{r['lng']},{r['lat']}", "geometryType": "esriGeometryPoint", "inSR": "4326", "distance": "2000",
                        "units": "esriSRUnit_Meter", "spatialRel": "esriSpatialRelIntersects", "outFields": fld, "returnDistinctValues": "true",
                        "returnGeometry": "false", "f": "json"})
        if res is None: return r, None
        codes = sorted({(f["attributes"].get(fld) or "").upper() for f in res.get("features", [])} - {""})
        x = {"res2": 1 if any(c.startswith(RES[r["s"]]) for c in codes) else 0}
        if r["s"] == "VIC" and any(c.startswith("UGZ") for c in codes): x["ugz2"] = 1
        return r, x
    done = fails = 0
    with ThreadPoolExecutor(4) as ex:   # 4 at a time: the map servers are slow per request
        for r, x in ex.map(one, todo[:limit]):
            done += 1
            if x is None: fails += 1; continue
            cache[str(r["id"])] = x
            if done % 100 == 0: json.dump(cache, open(P("edge-cache.json"), "w")); print("  ", done, "| no answer", fails, flush=True)
    json.dump(cache, open(P("edge-cache.json"), "w"))
    print("Town-edge check: cached", len(cache), "| near houses", sum(v.get("res2", 0) for v in cache.values()), "| near Urban Growth Zone", sum(v.get("ugz2", 0) for v in cache.values()))

if __name__ == "__main__":
    main()
