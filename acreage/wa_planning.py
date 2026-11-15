#!/usr/bin/env python3
"""WA planning check for each WA block (free SLIP map service, cached in wa-plan-cache.json): Region Scheme zones
within 2 km (Urban Deferred = land earmarked for future suburbs), advertised Region Scheme amendments within
3 km (rezonings in progress), and planned housing estates within 3 km (Perth and Peel Urban Land Development
Outlook 2023/24). Only covers the Perth, Peel and Greater Bunbury region schemes; elsewhere it finds nothing."""
import json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
B = "https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Property_and_Planning/MapServer/"
URBAN = re.compile(r"\burban\b", re.I)

def get(url, q):
    for t in range(3):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "acreage-finder"}), timeout=40).read())
            if "error" not in d: return d
        except Exception: pass
        time.sleep(3 * (t + 1))
    return None

def q(r, dist, fields):
    return {"geometry": f"{r['lng']},{r['lat']}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
            "distance": str(dist), "units": "esriSRUnit_Meter", "outFields": fields, "returnGeometry": "false", "f": "json"}

def main():
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: cache = json.load(open(P("wa-plan-cache.json")))
    except Exception: cache = {}
    todo = [r for r in d["listings"] if r["s"] == "WA" and r.get("lat") and not r.get("uo") and str(r["id"]) not in cache]
    print("WA planning: to do", len(todo))
    for i, r in enumerate(todo[:int(sys.argv[1]) if len(sys.argv) > 1 else 1000]):
        z = get(B + "48/query", {**q(r, 2000, "descriptio,reg_scheme"), "returnDistinctValues": "true"})
        am = get(B + "119/query", q(r, 3000, "proposal_n,status,descriptio,colloquial"))
        es = get(B + "139/query", q(r, 3000, "estate_nam,suburb,staging"))
        if z is None and am is None and es is None: continue
        x = {}
        zones = {(f["attributes"].get("descriptio") or "").strip() for f in (z or {}).get("features", [])}
        if zones: x["zones"] = sorted(zones)[:6]
        if any("deferred" in zz.lower() and "urban" in zz.lower() for zz in zones): x["ud2"] = 1
        ams = [f["attributes"] for f in (am or {}).get("features", []) if URBAN.search(f["attributes"].get("descriptio") or "")]
        if ams: x["amend"] = [[a.get("colloquial") or a.get("proposal_n"), a.get("status")] for a in ams[:2]]
        est = [f["attributes"] for f in (es or {}).get("features", [])]
        if est: x["estate"] = [[e.get("estate_nam") or e.get("suburb"), e.get("staging")] for e in est[:2]]
        cache[str(r["id"])] = x
        if i % 25 == 24: json.dump(cache, open(P("wa-plan-cache.json"), "w")); print("  ", i + 1, flush=True)
        time.sleep(0.3)
    json.dump(cache, open(P("wa-plan-cache.json"), "w"))
    print("WA planning: cached", len(cache), "| near Urban Deferred", sum(v.get("ud2", 0) for v in cache.values()),
          "| near an urban rezoning", sum(1 for v in cache.values() if v.get("amend")), "| near a planned estate", sum(1 for v in cache.values() if v.get("estate")))

if __name__ == "__main__":
    main()
