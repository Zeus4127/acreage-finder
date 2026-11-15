#!/usr/bin/env python3
"""Release check for the data: stops a release if the scan or scoring has gone wrong.
Compares with the last version that passed (checks/last-good.json). Exit 1 with reasons on failure.
  python3 -I checks/check_data.py            check only
  python3 -I checks/check_data.py --accept   check, and if it passes, remember these numbers as the new good"""
import json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = lambda f: os.path.join(HERE, f)

def stats():
    s = open(P("acreage-data.js")).read()
    d = json.loads(s.split("=", 1)[1].strip().rstrip(";"))
    L = d["listings"]; live = [r for r in L if not r.get("uo")]
    bad_num = sum(1 for r in L for k in ("p", "a", "fair", "gs") if isinstance(r.get(k), float) and (math.isnan(r[k]) or math.isinf(r[k])))
    return {"listings": len(L), "live": len(live), "priced": sum(1 for r in live if r.get("fair")), "scored": sum(1 for r in live if r.get("gs") is not None),
            "musts": sum(1 for r in live if r.get("gok")), "standouts": sum(1 for r in live if r.get("gstar")), "bad_numbers": bad_num,
            "bytes": len(s), "scanned": d.get("scanned", "")}

def main():
    now = stats(); fails = []
    try: good = json.load(open(P("checks/last-good.json")))
    except Exception: good = None
    if now["listings"] < 2000: fails.append(f"only {now['listings']} listings (expected 2,000+)")
    if now["bad_numbers"]: fails.append(f"{now['bad_numbers']} prices or scores are not real numbers")
    if now["live"] and now["priced"] / now["live"] < 0.6: fails.append(f"only {now['priced']} of {now['live']} blocks have a likely sale price")
    if now["live"] and now["scored"] / now["live"] < 0.8: fails.append(f"only {now['scored']} of {now['live']} blocks have a Growth score")
    if not 1 <= now["standouts"] <= 300: fails.append(f"{now['standouts']} Standouts (expected 1 to 300)")
    if now["bytes"] > 15_000_000: fails.append(f"data file is {now['bytes'] / 1e6:.1f} MB (limit 15)")
    if good:
        if now["listings"] < good["listings"] * 0.7: fails.append(f"listings fell from {good['listings']} to {now['listings']} (more than 30%)")
        if good["musts"] and now["musts"] < good["musts"] * 0.5: fails.append(f"blocks ticking the must-haves fell from {good['musts']} to {now['musts']}")
        if good["priced"] and now["priced"] < good["priced"] * 0.7: fails.append(f"priced blocks fell from {good['priced']} to {now['priced']}")
    if fails:
        print("DATA CHECK FAILED:\n - " + "\n - ".join(fails)); sys.exit(1)
    if "--accept" in sys.argv: json.dump(now, open(P("checks/last-good.json"), "w"), indent=1)
    print("DATA CHECK PASSED", {k: now[k] for k in ("listings", "priced", "musts", "standouts")})

if __name__ == "__main__":
    main()
