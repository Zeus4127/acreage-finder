#!/usr/bin/env python3
"""Queensland planning check for each QLD block (free state map service, cached in qld-plan-cache.json):
regional plan land use category (e.g. Rural Production Area, Rural Living, Urban Footprint), Significant Tourist
Activity Area (SEQ), Priority Agricultural Area, Strategic Environmental Area, and the Coordinator-General's big
projects within 40 km. Helps judge cabin or caravan-site potential. growth.py copies the result onto each listing."""
import json, math, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
B = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/StatePlanning/MapServer"

def get(url, params):
    q = url + "?" + urllib.parse.urlencode(params)
    for i in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(q, headers={"User-Agent": "acreage-finder"}), timeout=60).read())
        except Exception:
            time.sleep(3 * (i + 1))
    return None

def projects():
    f = P("ref/qld-projects.json")
    if os.path.exists(f) and time.time() - os.path.getmtime(f) < 30 * 86400: return json.load(open(f))
    d = get(B + "/25/query", {"where": "1=1", "outFields": "name,projectstatus,weblink", "returnGeometry": "true", "outSR": "4326", "maxAllowableOffset": "0.01", "f": "json"})
    out = []
    for ft in (d or {}).get("features", []):
        pts = [p for ring in (ft.get("geometry") or {}).get("rings", []) for p in ring]
        if not pts: continue
        a = ft["attributes"]
        out.append([a.get("name"), a.get("projectstatus"), round(sum(p[1] for p in pts) / len(pts), 4), round(sum(p[0] for p in pts) / len(pts), 4), a.get("weblink")])
    if out: json.dump(out, open(f, "w"))
    return out

def dev_areas():   # ShapingSEQ 2023 "SEQ development areas": the state's chosen future growth fronts
    f = P("ref/qld-dev-areas.json")
    if os.path.exists(f) and time.time() - os.path.getmtime(f) < 30 * 86400: return json.load(open(f))
    out = []
    for L in (105, 160):
        d = get(B + f"/{L}/query", {"where": "1=1", "outFields": "name", "returnGeometry": "true", "outSR": "4326", "maxAllowableOffset": "0.002", "f": "json"})
        for ft in (d or {}).get("features", []):
            pts = [[round(p[1], 4), round(p[0], 4)] for ring in (ft.get("geometry") or {}).get("rings", []) for p in ring]
            if pts: out.append([ft["attributes"].get("name"), pts[::max(1, len(pts) // 200)]])
    if out: json.dump(out, open(f, "w"))
    return out

def km(a, b, c, d):
    r = math.pi / 180
    return 6371 * 2 * math.asin(math.sqrt(math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((d - b) * r / 2) ** 2))

def main():
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: cache = json.load(open(P("qld-plan-cache.json")))
    except Exception: cache = {}
    todo = [r for r in d["listings"] if r["s"] == "QLD" and r.get("lat") and not r.get("uo") and str(r["id"]) not in cache]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    print("QLD planning: to check", len(todo), "| doing up to", limit)
    for i, r in enumerate(todo[:limit]):
        la, lo = r["lat"], r["lng"]; e = 0.002
        res = get(B + "/identify", {"geometry": f"{lo},{la}", "geometryType": "esriGeometryPoint", "sr": "4326", "layers": "all:15,20,120,140,165,245",
                                    "tolerance": "1", "mapExtent": f"{lo - e},{la - e},{lo + e},{la + e}", "imageDisplay": "100,100,96", "returnGeometry": "false", "f": "json"})
        if res is None: continue
        x = {}
        for h in res.get("results", []):
            L = h["layerId"]
            if L in (140, 165, 245): x["cat"] = h.get("value")
            elif L == 120: x["tour"] = 1
            elif L == 15: x["paa"] = 1
            elif L == 20: x["sea"] = 1
        if x.get("cat") != "Urban Footprint":   # path of growth: is the planned urban area within about 3 km?
            e2 = 0.05
            res2 = get(B + "/identify", {"geometry": f"{lo},{la}", "geometryType": "esriGeometryPoint", "sr": "4326", "layers": "all:140",
                                         "tolerance": "30", "mapExtent": f"{lo - e2},{la - e2},{lo + e2},{la + e2}", "imageDisplay": "100,100,96", "returnGeometry": "false", "f": "json"})
            if res2 and any(h.get("value") == "Urban Footprint" for h in res2.get("results", [])): x["uf3"] = 1
        cache[str(r["id"])] = x
        if i % 50 == 49: json.dump(cache, open(P("qld-plan-cache.json"), "w")); print("  ", i + 1, flush=True)
        time.sleep(0.25)
    json.dump(cache, open(P("qld-plan-cache.json"), "w"))
    pr = projects()
    near = {}
    for r in d["listings"]:
        if r["s"] != "QLD" or not r.get("lat"): continue
        c = sorted((km(r["lat"], r["lng"], p[2], p[3]), p) for p in pr)
        c = [(round(k), p[0], p[1]) for k, p in c if k <= 40][:2]
        if c: near[str(r["id"])] = c
    json.dump(near, open(P("qld-projects-near.json"), "w"))
    da = dev_areas(); dnear = {}
    for r in d["listings"]:
        if r["s"] != "QLD" or not r.get("lat"): continue
        best = min(((min(km(r["lat"], r["lng"], q[0], q[1]) for q in pts), n) for n, pts in da), default=None)
        if best and best[0] <= 25: dnear[str(r["id"])] = [round(best[0], 1), best[1]]
    json.dump(dnear, open(P("qld-devarea-near.json"), "w"))
    print("QLD planning: blocks within 25 km of a SEQ development area:", len(dnear))
    print("QLD planning: cached", len(cache), "| projects", len(pr), "| blocks near a project", len(near))

if __name__ == "__main__":
    main()
