#!/usr/bin/env python3
"""What did the areas that went up 10 times have in common? NSW Valuer-General sales of 10-200 acre blocks,
grouped into areas about 10 km wide: median $/acre in 2001-06 against 2022-26. Writes growth-jumps.json
(summary for the page) with the tree-change-belt rate: cheap areas 40-90 km from a city."""
import json, math, os, statistics, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); P = lambda f: os.path.join(HERE, f)
import growth as G

def main():
    s = json.load(open(P("nsw-sales.json"))); pl = json.load(open(P("ref/places.json")))
    cities = G.Grid([t for t in pl["town"] if t[3]], 3.0)
    C = 0.1; cells = {}
    for x in s:
        if not (10 <= x["a"] < 200) or not x.get("lat") or not x.get("p"): continue
        y = int(x["date"][:4]); k = (math.floor(x["lat"] / C), math.floor(x["lng"] / C))
        c = cells.setdefault(k, {"e": [], "l": [], "sub": collections.Counter(), "pts": []})
        v = x["p"] / x["a"]
        if y <= 2006: c["e"].append(v)
        elif y >= 2022: c["l"].append(v)
        c["sub"][x["sub"]] += 1
        if len(c["pts"]) < 30: c["pts"].append((x["lat"], x["lng"]))
    rows = []
    for c in cells.values():
        if len(c["e"]) >= 5 and len(c["l"]) >= 5:
            la = statistics.median(p[0] for p in c["pts"]); lo = statistics.median(p[1] for p in c["pts"])
            ci = cities.nearest(la, lo, 3)
            rows.append(dict(mult=statistics.median(c["l"]) / statistics.median(c["e"]), e=statistics.median(c["e"]), l=statistics.median(c["l"]),
                             sub=c["sub"].most_common(1)[0][0], city=ci[0] if ci else 999))
    q = sorted(r["e"] for r in rows); cheap = q[len(q) // 3]
    ten = [r for r in rows if r["mult"] >= 10]; rest = [r for r in rows if r["mult"] < 10]
    belt = [r for r in rows if r["e"] <= cheap and 40 <= r["city"] < 90]
    out = {"areas": len(rows), "median_multiple": round(statistics.median(r["mult"] for r in rows), 1), "ten_x": len(ten),
           "base_rate": round(100 * len(ten) / len(rows)), "belt_areas": len(belt), "belt_rate": round(100 * sum(r["mult"] >= 10 for r in belt) / max(1, len(belt))),
           "top_start": round(statistics.median(r["e"] for r in ten)), "other_start": round(statistics.median(r["e"] for r in rest)),
           "top": [[r["sub"], round(r["mult"], 1), round(r["e"]), round(r["l"])] for r in sorted(rows, key=lambda r: -r["mult"])[:15]]}
    json.dump(out, open(P("growth-jumps.json"), "w"), indent=1)
    print({k: v for k, v in out.items() if k != "top"})

if __name__ == "__main__":
    main()
