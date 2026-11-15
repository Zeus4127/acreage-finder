#!/usr/bin/env python3
"""Council population forecasts (free state government projections, saved in ref/popproj/): the forecast
yearly growth for about the next 15 years, by state and council. QLD (QGSO 2021-46, medium), TAS (Treasury
2024, medium), WA (WA Tomorrow 13, central band), SA (2016-36 release), NSW if the 2022 LGA file is present.
Victoria's file can't be downloaded automatically (the site blocks it). Writes ref/pop-forecast.json."""
import json, os, re
import openpyxl
HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, "ref", "popproj", f)

def norm(n):
    n = re.sub(r"\(.*?\)", "", str(n)).upper().replace("&", "AND")
    n = re.sub(r"\b(SHIRE|REGIONAL|COUNCIL|CITY OF|CITY|TOWN OF|TOWN|MUNICIPALITY|MUNICIPAL|DISTRICT|OF THE|ABORIGINAL)\b", " ", n)
    return re.sub(r"[^A-Z]", "", n)

def cagr(a, b, years): return round(((b / a) ** (1 / years) - 1) * 100, 2) if a and b and a > 0 else None

def main():
    out = {}
    if os.path.exists(P("qld-lga-2021-2046.xlsx")):
        ws = openpyxl.load_workbook(P("qld-lga-2021-2046.xlsx"), read_only=True, data_only=True)["Medium series"]
        for r in ws.iter_rows(min_row=6, values_only=True):
            if r[0] and isinstance(r[2], (int, float)) and isinstance(r[5], (int, float)): out["QLD|" + norm(r[0])] = cagr(r[2], r[5], 15)   # 2026 -> 2041
    if os.path.exists(P("tas-lga-2024.xlsx")):
        ws = openpyxl.load_workbook(P("tas-lga-2024.xlsx"), read_only=True, data_only=True)["Totals"]
        rows = list(ws.iter_rows(values_only=True)); hdr = rows[2]
        i26, i41 = hdr.index(2026), hdr.index(2041)
        for r in rows[3:]:
            if r[0] and isinstance(r[i26], (int, float)): out["TAS|" + norm(r[0])] = cagr(r[i26], r[i41], 15)
    if os.path.exists(P("wa-lga-2025-2041.xlsx")):
        ws = openpyxl.load_workbook(P("wa-lga-2025-2041.xlsx"), read_only=True, data_only=True)["Data - Total population"]
        v = {}
        for r in ws.iter_rows(min_row=9, values_only=True):
            if r[0] and r[2] == "Central" and r[1] in (2026, 2041): v.setdefault(r[0], {})[r[1]] = r[3]
        for k, y in v.items():
            if 2026 in y and 2041 in y: out["WA|" + norm(k)] = cagr(y[2026], y[2041], 15)
    if os.path.exists(P("sa-lga-2016-2036.xlsx")):
        ws = openpyxl.load_workbook(P("sa-lga-2016-2036.xlsx"), read_only=True, data_only=True)["Projected population"]
        for r in ws.iter_rows(min_row=11, values_only=True):
            if r[1] and r[2] == "Persons" and isinstance(r[5], (int, float)): out["SA|" + norm(r[1])] = cagr(r[5], r[7], 10)   # 2026 -> 2036
    nsw = [f for f in os.listdir(P("")) if f.startswith("nsw-lga")]
    if nsw:
        wb = openpyxl.load_workbook(P(nsw[0]), read_only=True, data_only=True)
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            hi = next((i for i, r in enumerate(rows[:30]) if r and 2026 in r and 2041 in r), None)
            if hi is None: continue
            h = rows[hi]; i26, i41 = h.index(2026), h.index(2041)
            for r in rows[hi + 1:]:
                nm = next((c for c in r[:3] if isinstance(c, str) and len(c) > 2), None)
                if nm and isinstance(r[i26], (int, float)) and isinstance(r[i41], (int, float)) and r[i26] > 0:
                    out.setdefault("NSW|" + norm(nm), cagr(r[i26], r[i41], 15))
            break
    out = {k: v for k, v in out.items() if v is not None}
    json.dump(out, open(os.path.join(HERE, "ref", "pop-forecast.json"), "w"), indent=0, sort_keys=True)
    from collections import Counter
    print("population forecasts:", len(out), dict(Counter(k.split("|")[0] for k in out)))

if __name__ == "__main__":
    main()
