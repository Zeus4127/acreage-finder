#!/usr/bin/env python3
"""Cross-check for Queensland with a second, independent free source: the Valuer-General's land valuation changes
for every council since 2002 (data.qld.gov.au, "Historical trends in land valuations", saved in ref/qld-vg/).
Each council's % change at each revaluation is chained into an index. Tests: (1) councils that rose least in
2002-2013 rose most in 2013-2026; (2) councils cheap per hectare in 2015 (Bendigo farmland report) rose most
by the Valuer-General's figures 2015-2026. Writes growth-check-qld.json."""
import json, os, random, statistics, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
IDS = {"new": "2fd7c102-cafc-4d16-a6a5-ff4ed7c61c16", "old": "74f9b06c-4917-4ee9-829c-a6af1c3cb3e9"}

def records(k):
    f = P(f"ref/qld-vg/{k}.json")
    if not os.path.exists(f):
        url = f"https://www.data.qld.gov.au/api/3/action/datastore_search?resource_id={IDS[k]}&limit=32000"
        open(f, "w").write(urllib.request.urlopen(url, timeout=60).read().decode())
    return json.load(open(f))["result"]["records"]

def num(v):
    try: return float(v)
    except Exception: return None

def chain(rec, y0, y1):   # index change over valuations dated y0 < year <= y1
    m, n = 1.0, 0
    for y in range(y0 + 1, y1 + 1):
        v = num(rec.get(str(y)))
        if v is not None: m *= 1 + v / 100; n += 1
    return m, n

def rk(a): return np.argsort(np.argsort(a)).astype(float)
def spear(a, b): return float(np.corrcoef(rk(a), rk(b))[0, 1])
def shuffle_p(a, b, rho):
    rnd = random.Random(5); b = list(b); c = 0
    for _ in range(2000):
        rnd.shuffle(b); c += spear(a, b) >= rho
    return (c + 1) / 2001

def main():
    new = {r["Local Government Area"].upper(): r for r in records("new") if r.get("LGA_Code")}
    old = records("old")
    early = {}   # 2002-2009 changes, old councils averaged into today's councils
    for r in old:
        to = (r.get("Post-amalgamation LGA") or r.get("LGA") or "").upper()
        if not to or r["LGA"].startswith("Total"): continue
        m, n = chain(r, 2001, 2009)
        if n: early.setdefault(to, []).append(m)
    rows = []
    for name, r in new.items():
        a1, na1 = chain(r, 2009, 2013); b, nb = chain(r, 2013, 2026)
        if name not in early or not na1 or not nb: continue
        a = statistics.median(early[name]) * a1
        rows.append(dict(lga=name, ga=(a ** (1 / 12) - 1) * 100, gb=(b ** (1 / 13) - 1) * 100, b15=(chain(r, 2015, 2026)[0] ** (1 / 11) - 1) * 100))
    out = {"source": "Queensland Valuer-General, historical trends in land valuations (data.qld.gov.au)", "councils": len(rows)}
    x, y = [-r["ga"] for r in rows], [r["gb"] for r in rows]
    rho = spear(np.array(x), np.array(y)); out["not_boomed"] = {"rank_match": round(rho, 2), "p": round(shuffle_p(x, y, rho), 4), "n": len(rows)}
    print(f"QLD not-boomed rule: {len(rows)} councils | rank match {rho:+.2f} p={out['not_boomed']['p']}")
    h = json.loads(open(P("history-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    lv = {x["lga"].upper(): (x["path"].get("2015") or x["path"].get("2014")) for x in h["lgas"] if x["state"] == "QLD"}
    R = [r for r in rows if lv.get(r["lga"])]
    if len(R) >= 8:
        x, y = [-lv[r["lga"]] for r in R], [r["b15"] for r in R]
        rho = spear(np.array(x), np.array(y)); out["cheap"] = {"rank_match": round(rho, 2), "p": round(shuffle_p(x, y, rho), 4), "n": len(R)}
        print(f"QLD cheap rule (Bendigo 2015 price vs Valuer-General growth 2015-26): {len(R)} councils | rank match {rho:+.2f} p={out['cheap']['p']}")
    json.dump(out, open(P("growth-check-qld.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
