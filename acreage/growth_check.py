#!/usr/bin/env python3
"""Honest check of the Growth score, the Track Edge way: judge it on years it was never tuned on.

NSW 10-100 acre sales (Valuer General) grouped into areas (0.25 degree squares). Two decades:
  A (older):  2002-05 prices vs 2011-14 prices   <- the score's weights were NOT chosen on these years
  B (newer):  2012-15 prices vs 2022-25 prices   <- the years the weights were chosen on
Tests: (1) does the score's area part rank decade A correctly; (2) shuffle test: the same score against
shuffled growth 2000 times (it must do much better than shuffled); (3) fit on A only, predict B (walk forward);
(4) momentum: did areas that grew fast in A keep growing in B. Writes growth-check.json for the page.
"""
import json, math, os, random, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import growth as G
P = lambda f: os.path.join(HERE, f)

def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b)); return float(np.corrcoef(ra, rb)[0, 1])

def build():
    s = json.load(open(P("nsw-sales.json")))
    pl = json.load(open(P("ref/places.json"))); life = json.load(open(P("ref/lifestyle.json")))
    sua = G.Grid(pl["sua"], 2.0); cities = G.Grid([t for t in pl["town"] if t[3]], 3.0); towns = G.Grid(pl["town"])
    coast = G.Grid(pl["coast"], 1.0); parks = G.Grid(pl["parks"], 1.0)
    wine = G.Grid([[w[1], w[2], w[0]] for w in life["wine"]], 2.0); hol = G.Grid([[h[1], h[2], h[0]] for h in life["holiday"]], 2.0)
    hosp = G.Grid([h for h in pl["hosp"] if h[3]], 1.0)
    pe = lambda d, p: max(0.0, d - math.sqrt(max(p[4], 1) / 100 / math.pi))
    W = {"a0": (2002, 2005), "a1": (2011, 2014), "b0": (2012, 2015), "b1": (2022, 2025)}
    C = 0.25; cells = {}; state = {k: [] for k in W}
    for x in s:
        if not (10 <= x["a"] < 100) or not x.get("lat") or not x.get("p"): continue
        y = int(x["date"][:4]); k = (math.floor(x["lat"] / C), math.floor(x["lng"] / C))
        c = cells.setdefault(k, {w: [] for w in W} | {"pts": []})
        for w, (lo, hi) in W.items():
            if lo <= y <= hi: c[w].append(x["p"] / x["a"]); state[w].append(x["p"] / x["a"])
        if len(c["pts"]) < 40: c["pts"].append((x["lat"], x["lng"]))
    sm = {w: statistics.median(v) for w, v in state.items()}
    N = 8; rows = []
    for k, c in cells.items():
        la = statistics.median(p[0] for p in c["pts"]); lo = statistics.median(p[1] for p in c["pts"])
        f = lambda grid, reach=2, fn=None: (grid.nearest(la, lo, reach, fn) or (9999, None))[0]
        r = dict(city=G.mins(f(cities)), hol=G.mins(f(hol, 1)), coast=f(coast), sua=G.mins(f(sua)), town=G.mins(f(towns)),
                 hosp=G.mins(f(hosp, 1)), park=f(parks, 1, pe), wine=f(wine, 1))
        for d in ("a", "b"):
            e, l = c[d + "0"], c[d + "1"]
            if len(e) >= N and len(l) >= N:
                r["g" + d] = ((statistics.median(l) / statistics.median(e)) ** (1 / 9.5) - 1) * 100
                r["cheap" + d] = statistics.median(e) / sm[d + "0"]
        if "ga" in r or "gb" in r: rows.append(r)

    def area_pts(r, d):   # the area part of the live Growth score, same points as growth.py
        cm, hm, cst, smn, tm, hp, pk, wd, ca = r["city"], r["hol"], r["coast"], r["sua"], r["town"], r["hosp"], r["park"], r["wine"], r["cheap" + d]
        return ((12 if cm <= 90 else 10 if cm <= 150 else 5 if cm <= 240 else 0) + (9 if hm <= 30 else 7 if hm <= 60 else 2 if hm <= 120 else 0)
                + (6 if cst <= 20 else 3 if cst <= 60 else 2 if cst <= 150 else 0) + (6 if smn <= 40 else 4 if smn <= 60 else 2 if smn <= 90 else 0)
                + (3 if tm <= 15 else 1 if tm <= 25 else 0) + (2 if hp <= 45 else 0) + (6 if pk <= 5 else 3 if pk <= 15 else 1 if pk <= 35 else 0)
                + (2 if wd <= 25 else 1 if wd <= 50 else 0) + (5 if ca <= 0.7 else 3 if ca <= 0.9 else 0))

    return rows, area_pts

def main():
    rows, area_pts = build()
    out = {}
    def judge(name, d, score, growth):
        sc, g = np.array(score, float), np.array(growth, float)
        rho = spearman(sc, g); rnd = random.Random(7); sh = []
        for _ in range(2000):
            gg = list(g); rnd.shuffle(gg); sh.append(spearman(sc, gg))
        p = (sum(1 for v in sh if v >= rho) + 1) / 2001
        q = np.quantile(sc, [0.2, 0.8]); top = g[sc >= q[1]]; bot = g[sc <= q[0]]
        out[name] = dict(areas=len(g), rank_match=round(rho, 2), shuffled_best=round(float(np.quantile(sh, 0.99)), 2), p=round(p, 4),
                         top_fifth=round(float(np.median(top)), 2), bottom_fifth=round(float(np.median(bot)), 2), all=round(float(np.median(g)), 2))
        print(f"{name}: {len(g)} areas | rank match {rho:+.2f} (shuffled 99th pct {out[name]['shuffled_best']:+.2f}, p={p:.4f}) | "
              f"growth/yr top fifth {out[name]['top_fifth']}% vs bottom fifth {out[name]['bottom_fifth']}% (all {out[name]['all']}%)")

    A = [r for r in rows if "ga" in r]; B = [r for r in rows if "gb" in r]
    judge("1_live_score_on_older_decade", "a", [area_pts(r, "a") for r in A], [r["ga"] for r in A])
    judge("live_score_on_tuning_decade", "b", [area_pts(r, "b") for r in B], [r["gb"] for r in B])
    # walk forward: fit a simple model on decade A only, then score decade B
    ks = ["city", "hol", "coast", "sua", "town", "hosp", "park", "wine"]
    feat = lambda r, d: [math.log(1 + min(r[k], 2000)) for k in ks] + [math.log(r["cheap" + d])]
    XA = np.array([feat(r, "a") for r in A]); mu, sd = XA.mean(0), XA.std(0) + 1e-9
    beta = np.linalg.lstsq(np.c_[np.ones(len(A)), (XA - mu) / sd], np.array([r["ga"] for r in A]), rcond=None)[0]
    XB = np.array([feat(r, "b") for r in B]); predB = np.c_[np.ones(len(B)), (XB - mu) / sd] @ beta
    judge("3_fit_on_older_predict_newer", "b", list(predB), [r["gb"] for r in B])
    out["older_decade_weights"] = {k: round(float(v), 2) for k, v in zip(ks + ["cheap"], beta[1:])}
    # momentum: did fast growers keep growing?
    AB = [r for r in rows if "ga" in r and "gb" in r]
    judge("4_momentum_older_growth_predicts_newer", "b", [r["ga"] for r in AB], [r["gb"] for r in AB])
    # each factor on its own, in both decades (closer = better, so distance is negated)
    fac = {}
    for k in ks + ["cheap"]:
        v = []
        for d, R in (("a", A), ("b", B)):
            x = [-(r["cheap" + d] if k == "cheap" else min(r[k], 2000)) for r in R]; v.append(round(spearman(np.array(x), np.array([r["g" + d] for r in R])), 2))
        fac[k] = {"older": v[0], "newer": v[1], "holds_up": v[0] > 0.05 and v[1] > 0.05}
    out["factors"] = fac
    print("factor rank match (older, newer):", {k: (v["older"], v["newer"]) for k, v in fac.items()})
    json.dump(out, open(P("growth-check.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
