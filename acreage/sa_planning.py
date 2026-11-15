#!/usr/bin/env python3
"""SA planning check for each SA block (free PlanSA map service at location.sa.gov.au, cached in sa-plan-cache.json):
the block's zone (Planning and Design Code), rezonings (Code Amendments) within 3 km, especially rural land being
rezoned for housing, and Greenfield land-supply areas within 2 km. growth.py turns these into growth-path signs."""
import json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
B = "https://location.sa.gov.au/server6/rest/services/GrowthManagementPublic/"
HOUSING = re.compile(r"neighbourhood|residential|township|master planned|suburb|housing|rural living", re.I)
RURAL = re.compile(r"rural|productive|peri-urban|primary production|deferred", re.I)

def get(url, q):
    for t in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "acreage-finder"}), timeout=40).read())
            if "error" not in d: return d
        except Exception: pass
        time.sleep(3 * (t + 1))
    return None

def q(r, dist=None, fields="*"):
    p = {"geometry": f"{r['lng']},{r['lat']}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
         "outFields": fields, "returnGeometry": "false", "f": "json"}
    if dist: p.update(distance=str(dist), units="esriSRUnit_Meter")
    return p

def main():
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: cache = json.load(open(P("sa-plan-cache.json")))
    except Exception: cache = {}
    todo = [r for r in d["listings"] if r["s"] == "SA" and r.get("lat") and not r.get("uo") and str(r["id"]) not in cache]
    print("SA planning: to do", len(todo))
    for i, r in enumerate(todo[:int(sys.argv[1]) if len(sys.argv) > 1 else 1000]):
        z = get(B + "CodeAmendments_BaseLayers_plansadb/MapServer/2/query", q(r, fields="name"))
        ca = get(B + "Code_Amendments_PUBLIC/MapServer/1/query", q(r, 3000, "codeamendment,status,currentzone,proposedzone,statewide"))
        gf = get(B + "Greenfield/MapServer/0/query", {**q(r, 2000, "objectid"), "returnCountOnly": "true"})
        if z is None and ca is None: continue
        x = {}
        if z and z.get("features"): x["zone"] = z["features"][0]["attributes"].get("name")
        rez = []
        for f in (ca or {}).get("features", []):
            a = f["attributes"]
            if a.get("statewide") == "Yes": continue
            cur, new = a.get("currentzone") or "", a.get("proposedzone") or ""
            rez.append([a.get("codeamendment"), a.get("status"), 1 if (RURAL.search(cur) and HOUSING.search(new)) else 0])
        if rez: x["rez"] = rez[:3]
        if gf and gf.get("count"): x["green"] = 1
        cache[str(r["id"])] = x
        if i % 25 == 24: json.dump(cache, open(P("sa-plan-cache.json"), "w")); print("  ", i + 1, flush=True)
        time.sleep(0.3)
    json.dump(cache, open(P("sa-plan-cache.json"), "w"))
    print("SA planning: cached", len(cache), "| near a rural-to-housing rezoning", sum(1 for v in cache.values() if any(z[2] for z in v.get("rez", []))),
          "| near greenfield land", sum(v.get("green", 0) for v in cache.values()))

if __name__ == "__main__":
    main()
