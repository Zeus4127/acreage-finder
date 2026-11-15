#!/usr/bin/env python3
"""NSW official future-growth land (free NSW Planning Portal map service): Land Release Areas and Strategic
Urban Growth Areas from council plans. Saves outlines (simplified) to ref/nsw-growth-areas.json."""
import json, os, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
B = "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/Planning_Portal_Local_Provisions/MapServer/%d/query"
def get(url, params):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=90).read())
        except Exception: time.sleep(5 * (i + 1))
out = []
for L, kind in ((493, "Land Release Area"), (571, "Strategic Urban Growth Area")):
    d = get(B % L, {"where": "1=1", "outFields": "EPI_NAME,LGA_NAME,LAY_CLASS", "returnGeometry": "true", "outSR": "4326", "maxAllowableOffset": "0.002", "f": "json"})
    for ft in (d or {}).get("features", []):
        pts = [[round(p[1], 4), round(p[0], 4)] for ring in (ft.get("geometry") or {}).get("rings", []) for p in ring]
        a = ft["attributes"]
        if pts: out.append({"kind": kind, "lga": a.get("LGA_NAME"), "name": a.get("LAY_CLASS") or a.get("EPI_NAME"), "pts": pts[::max(1, len(pts) // 150)]})
    print(kind, sum(1 for o in out if o["kind"] == kind))
if out: json.dump(out, open(P("ref/nsw-growth-areas.json"), "w"))
