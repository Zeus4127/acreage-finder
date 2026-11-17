# Acreage Finder: handover to a new session

Written 17 Nov 2026 so a fresh session can finish the app and website and get them running on their own.

## First steps in the new session
1. **Get the latest work.** The last commits on branch `ccr-37547555-829az5` may not be on GitHub yet (pushes kept failing with 403).
   If the upload `acreage-finder-changes.bundle` is attached, apply it:
   `git fetch acreage-finder-changes.bundle ccr-37547555-829az5:handover && git checkout ccr-37547555-829az5 && git merge --ff-only handover`
   then push the branch. Check: `acreage/HANDOVER.md` exists and `git log` shows "Home rebuilt in the Mega Electrics structure".
2. **Signing key for the Android app.** The owner keeps `acreage.jks` and `acreage.pass` privately. Never commit them.
   Put them outside the repo (for example in `~/keys/`). Build with
   `cd acreage/android && ACREAGE_KEYSTORE=~/keys/acreage.jks ACREAGE_KSPASS="$(cat ~/keys/acreage.pass)" bash build.sh`
   The package must stay `au.zac.acreagefinder`, signed with the same key, or phones won't accept the update.
3. **Read `acreage/CLAUDE.md`** and follow it: publish only on RELEASE PASSED, never loosen a check, back up before editing.

## Where things are
- Website: one page, `acreage/acreage.html`. It's built by `build_page.py` and released only through `./release.sh <out.html>`, which runs
  `checks/check_data.py` and `checks/check_page.js` (phone and desktop).
- Live page: claude.ai artifact https://claude.ai/artifact/8MPdWAJGMGGWvUNDMK8AF8. It's private: share it from its Share menu.
- Android app: `acreage/android/`, now version 3.1 (versionCode 21). Bump both for every build.
- Daily data: `run_daily.sh` (full scan, about 40 min) and `run_hourly.sh` (quick refresh). Both end with release.sh.
- Methods and test results: `acreage/README.md`.

## Done
- About 5,460 blocks of 10+ acres from Farmbuy and Farm Property, scanned daily, with price cuts and sales tracked.
- Growth score, tested on 25 years of sales; likely sale price, tested on newest sales (within 20% about 4 in 10).
- Drive times, water, rain, slope, flood/fire, zoning, planning and growth paths, population forecasts.
- Search, map, compare, saved blocks, my rules, alerts feed, Market pulse, Insights, Check any listing.
- Design: Home rebuilt in the owner's Mega Electrics site structure (navy and gold land theme). It goes simple at the top, charts in the
  middle ("Look closer"), and workings at the bottom ("How it works"). It has charts on Home, the block page, Search, Saved and Insights.
- 17 Nov price test: 60 variants were tried and none beat the current method on the newest sales, so it was kept (see README).

## State on 17 Nov 2026 (after the Fable pass)
- Website version 54 and app 3.0 (versionCode 20). Every screen now has the same business structure: a dark page header with key
  numbers, then content. Search has a filter sidebar on desktop. The block page has a sticky side card (asking, likely sale, offer,
  walk-away, buttons) on desktop.
- Fixed: Home said "5,008 new in 3 days" (it counted the day tracking began; now 44). The data check panel now says "Asking price shown 70%"
  and "Likely sale price 99%" (it used to label the 70% as "Priced"). The growth rank no longer says "higher than 100%".
- `run_daily.sh` and `run_hourly.sh` call `publish_site.sh` after RELEASE PASSED. It does nothing until `acreage/site-repo.txt` exists.

## DANGER: do not touch this repo's GitHub Pages
`bargain-finder` main already serves the caravan **Bargain Finder** website with GitHub Pages. Never switch this repo's Pages source and
never publish Acreage Finder into it. Acreage Finder's public site needs its **own repo**.

## Still to do (all need the owner)
1. **GitHub push is refused (403)** for git in every cloud session, old or new, even though the GitHub tools can read the repo. The Claude
   GitHub App is installed on Zeus4127 but this repo is probably not in its repository list. Owner: GitHub → Settings → Applications →
   Claude → Configure → Repository access → add `bargain-finder` (or All repositories). Then `git push -u origin ccr-37547555-829az5`.
   Until then the app can't get fresh data (it reads `acreage/acreage-data.js` from this branch on raw.githubusercontent.com).
2. **Public website:** owner creates an empty public repo (for example `acreage-finder`), turns on Pages for main, and gives the Claude app
   access to it. Put its address in `acreage/site-repo.txt`. The refresh scripts then publish to it by themselves.
   Until then, share the claude.ai artifact from its Share menu.
3. **Phone alerts:** set the ntfy topic on the phone only. Never store it in a file.
4. Real-phone test of app 3.0.
5. Can't reach 85/100 within the rules: price accuracy (needs paid sales data) and coverage (Domain and realestate.com.au are off-limits).

## Scheduled tasks (already running)
- "Acreage Finder daily refresh (this chat)", 3:40 am Brisbane, and "Acreage Finder midday + evening refresh (weekdays)", 12:07 and 5:07 pm.
  Both fire into session_018H8UUA2PVZm6rSG4DDuejH, which holds the signing key and the scratchpad page. If that session is ever lost,
  re-create them for a new session and change the scratchpad path in their prompts.

## Standing rules from the owner
Free tools only. Never scrape Facebook, Gumtree, Domain or realestate.com.au; never get around bot checks. No keys, passwords or ntfy topics
in any file. Light theme, no purple or pink. Plain, simple words. Don't waste usage.
