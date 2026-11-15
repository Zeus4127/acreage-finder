#!/usr/bin/env python3
"""The Growth score check for every state, not just NSW. Uses the Bendigo Bank farmland reports already in
history-data.js: council (LGA) median $/ha in about 2005, 2015 and 2025, all states. Decade A = 2005->2015,
decade B = 2015->2025. Tests the two rules the NSW check found: (1) councils cheap against their state caught up
faster, (2) councils that hadn't boomed yet grew faster next decade. Ranks are compared within each state, and each
result must beat 2000 shuffles. Writes growth-check-states.json."""
import json, os, random, statistics
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)

def rk(a): return np.argsort(np.argsort(a)).astype(float)
def spear(a, b): return float(np.corrcoef(rk(a), rk(b))[0, 1])
def pt(p, ys):
    for y in ys:
        if str(y) in p: return p[str(y)], y
    return None, None

def main():
    h = json.loads(open(P("history-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    rows = []
    for x in h["lgas"]:
        p = x.get("path", {})
        (v0, y0), (v1, y1), (v2, y2) = pt(p, (2005, 2004)), pt(p, (2015, 2014)), pt(p, (2025, 2024))
        if not (v0 and v1 and v2): continue
        rows.append(dict(s=x["state"], lga=x["lga"], v0=v0, v1=v1, v2=v2, ga=((v1 / v0) ** (1 / (y1 - y0)) - 1) * 100, gb=((v2 / v1) ** (1 / (y2 - y1)) - 1) * 100))
    by = {}
    for r in rows: by.setdefault(r["s"], []).append(r)
    for st, R in by.items():   # cheap = council price against its state's middle council at the start of each decade
        m0, m1 = statistics.median(r["v0"] for r in R), statistics.median(r["v1"] for r in R)
        for r in R: r["cheapA"], r["cheapB"] = r["v0"] / m0, r["v1"] / m1
    out = {"source": h["source"], "councils": len(rows), "tests": {}}
    def test(name, R, score, growth):
        # within-state ranks so a whole state booming doesn't count as skill
        sc, g = np.zeros(len(R)), np.zeros(len(R))
        for st in {r["s"] for r in R}:
            ix = [i for i, r in enumerate(R) if r["s"] == st]
            if len(ix) < 4: continue
            sc[ix] = rk(np.array([score(R[i]) for i in ix])) / (len(ix) - 1); g[ix] = rk(np.array([growth(R[i]) for i in ix])) / (len(ix) - 1)
        rho = spear(sc, g); rnd = random.Random(3); sh = []
        for _ in range(2000):
            gg = g.copy()
            for st in {r["s"] for r in R}:   # shuffle within each state
                ix = [i for i, r in enumerate(R) if r["s"] == st]; vals = list(gg[ix]); rnd.shuffle(vals); gg[ix] = vals
            sh.append(spear(sc, gg))
        p = (sum(1 for v in sh if v >= rho) + 1) / 2001
        per = {}
        for st in sorted({r["s"] for r in R}):
            S = [r for r in R if r["s"] == st]
            if len(S) >= 6: per[st] = round(spear(np.array([score(r) for r in S]), np.array([growth(r) for r in S])), 2)
        q = np.quantile(sc, 0.8); top = [growth(R[i]) for i in range(len(R)) if sc[i] >= q]
        out["tests"][name] = dict(rank_match=round(rho, 2), p=round(p, 4), by_state=per, top_fifth_growth=round(statistics.median(top), 2), all_growth=round(statistics.median(growth(r) for r in R), 2))
        print(f"{name}: {len(R)} councils | rank match {rho:+.2f} p={p:.4f} | by state {per} | top fifth {out['tests'][name]['top_fifth_growth']}%/yr vs all {out['tests'][name]['all_growth']}%")
    test("cheap_then_growth_2005_15", rows, lambda r: -r["cheapA"], lambda r: r["ga"])
    test("cheap_then_growth_2015_25", rows, lambda r: -r["cheapB"], lambda r: r["gb"])
    test("not_boomed_2005_15_then_growth_2015_25", rows, lambda r: -r["ga"], lambda r: r["gb"])
    json.dump(out, open(P("growth-check-states.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
