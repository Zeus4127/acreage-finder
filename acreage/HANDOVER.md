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
- Android app: `acreage/android/`, now version 2.9 (versionCode 19). Bump both for every build.
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

## Still to do to make it run on its own
1. **Push to GitHub**, then publish the public site: push `/home/user/site-gh-pages` (or re-create it with `publish_site.sh`) to the
   `gh-pages` branch. The owner turns on Pages under Settings → Pages → gh-pages. The site will be at https://zeus4127.github.io/bargain-finder/.
2. **Add `publish_site.sh` to `run_daily.sh` and `run_hourly.sh`** after RELEASE PASSED, so the public site updates itself.
3. **Point the app at the public site's data**, so the installed app gets fresh listings every day without a new APK.
4. **Scheduled tasks.** The daily and midday/evening refresh tasks currently fire into the old session. Re-create them for the new
   session (or a fresh session each time) once GitHub works.
5. **Phone alerts.** These need an ntfy topic, which the owner sets on the phone. Never store it in a file.
6. Restyle Search, Saved, Insights, More and the block page in the same Mega-style structure as Home (keep phone Home under 6,000 px).
7. Real-phone test of the APK. Things that can't reach 85/100 within the rules: price accuracy (needs paid sales data) and coverage
   (Domain and realestate.com.au are off-limits).

## Standing rules from the owner
Free tools only. Never scrape Facebook, Gumtree, Domain or realestate.com.au; never get around bot checks. No keys, passwords or ntfy topics
in any file. Light theme, no purple or pink. Plain, simple words. Don't waste usage.
