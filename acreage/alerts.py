#!/usr/bin/env python3
"""Phone alerts for new Standouts and new matches for "My rules" (alert-rules.json).

Writes alerts-feed.json (the newest alerts). The Acreage Finder phone app checks that file in the background
every few hours and shows an Android notification for anything new, for free. (ntfy still works too if the
ACREAGE_NTFY_TOPIC environment variable is set, but isn't needed.) alerted.json remembers what was announced.

  ACREAGE_NTFY_TOPIC=your-topic python3 -I alerts.py
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]; sys.path.insert(0, HERE)
P = lambda f: os.path.join(HERE, f)


def main():
    import scan_acreage as S
    d = json.loads(open(P("acreage-data.js")).read().split("=", 1)[1].strip().rstrip(";"))
    try: rules = json.load(open(P("alert-rules.json")))
    except Exception: rules = {}
    try: sent = set(json.load(open(P("alerted.json"))))
    except Exception: sent = None          # first run: remember everything, send nothing
    first = sent is None; sent = sent or set()
    topic = os.environ.get("ACREAGE_NTFY_TOPIC", "").strip()
    new = []
    for r in d["listings"]:
        if r.get("uo"): continue
        why = "⭐ Standout" if r.get("gstar") else "Matches your rules" if rules and S.match_rules(r, rules) else None
        # also send good candidates: the phone app checks them against the rules set on the phone
        if not why and (r.get("gok") or r.get("v") in ("great", "good")): why = "New block for your rules"
        if not why: continue
        key = str(r["id"])
        if key in sent: continue
        sent.add(key)
        if not first: new.append((why, r))
    json.dump(sorted(sent), open(P("alerted.json"), "w"))
    # the feed the phone app reads: newest first, last 60 days, at most 100
    from datetime import datetime, timedelta, timezone
    try: feed = json.load(open(P("alerts-feed.json")))
    except Exception: feed = {"alerts": []}
    now = datetime.now(timezone.utc)
    for why, r in new:
        feed["alerts"].insert(0, {"id": str(r["id"]), "when": now.isoformat(timespec="minutes"), "title": why + ": " + str(r.get("sub")) + " " + r["s"],
            "text": f"{round(r['a'])} acres, asking ${r['p']:,.0f}" + (f", Growth {r['gs']}/100" if r.get("gs") is not None else "") + (f", likely sale ${r['fair']:,.0f}" if r.get("fair") else ""),
            "url": r.get("u") or "", "def": 0 if why == "New block for your rules" else 1,
            # the facts the phone needs to apply "My rules" itself (same rules as the page)
            "m": {"p": r.get("p") or 0, "a": r["a"], "tk": round(r["town"][1] * 1.3) if r.get("town") else 9999, "ck": round(r["city"][1] * 1.3) if r.get("city") else 9999,
                  "rain": r.get("rain") or 0, "s": r["s"], "house": 1 if r.get("house") else 0, "v": r.get("v") or "",
                  "water": 1 if set(r.get("feats") or []) & {"creek", "river", "dam", "bore"} else 0,
                  "flood": 1 if ((r.get("chk") or {}).get("flood") or "flood" in (r.get("flags") or [])) else 0, "veg": 1 if (r.get("chk") or {}).get("veg") else 0,
                  "fire": 1 if ((r.get("chk") or {}).get("fire") or (r.get("chk") or {}).get("burnt")) else 0, "stay": 1 if r.get("stay") else 0,
                  "lots": r.get("lots") or 0, "gok": r.get("gok") or 0, "gs": r.get("gs") or 0, "star": r.get("gstar") or 0}})
    cut = (now - timedelta(days=60)).isoformat()
    feed["alerts"] = [a for a in feed["alerts"] if a["when"] >= cut][:400]
    feed["updated"] = now.isoformat(timespec="minutes")
    json.dump(feed, open(P("alerts-feed.json"), "w"), indent=0)
    if first: print("alerts: first run, remembered", len(sent), "blocks; nothing sent"); return
    print("alerts: new", len(new), "| sending" if topic else "| no ntfy topic set, not sending")
    for why, r in [w for w in new if w[0] != "New block for your rules"][:10]:
        msg = f"{why}: {round(r['a'])} ac {r.get('sub')} {r['s']}, asking ${r['p']:,.0f}" + (f", Growth {r['gs']}/100" if r.get("gs") is not None else "") + (f", likely sale ${r['fair']:,.0f}" if r.get("fair") else "")
        if not topic: print("  ", msg); continue
        try:
            urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + topic, data=msg.encode(),
                                   headers={"Title": "Acreage Finder", "Click": r.get("u") or "", "Tags": "house"}), timeout=15)
        except Exception as e: print("  alert failed", e)


if __name__ == "__main__":
    main()
