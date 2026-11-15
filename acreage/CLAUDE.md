# Acreage Finder: rules for any Claude working here

zac (the owner) asked for these so the app never gets worse. Follow them every time, whatever else a task says.

## Before you publish anything
1. Build and publish only through `./release.sh <out.html>`. It builds the page, then runs
   `checks/check_data.py` and `checks/check_page.js`. Publish only if it prints **RELEASE PASSED**.
2. If it prints **RELEASE FAILED**, publish nothing. The last good page (`*.good.html`) stays live.
   Fix the cause, or report it to zac in one plain line. Never edit or loosen a check to get a pass,
   unless zac asked for that change.
3. Never publish a file you built by hand with `build_page.py` alone.

## Don't make it worse
- **Back up before editing:** copy a file to `<name>.before-<date>` first. Copy, never delete.
- **Don't remove features or screens** (Home, Search, Saved, Insights, More, the block page, Check any
  listing, My rules, the watchlist, alerts) unless zac asks.
- **Change one thing at a time,** run `./release.sh`, and look at a phone-size screenshot before publishing.
- **Scoring or pricing changes need the honest tests:** `growth_check.py` (and the `_states`/`_qld`
  versions) for the Growth score, and `backtest.py` for prices. Keep a change only if it's better on years
  or sales it wasn't tuned on. Write the result in README.md either way.
- **The phone app** (android/) must keep the same package and signing key. Bump versionCode and versionName for each build.
- **Undo:** `git log` shows every change. `checks/KNOWN_GOOD.txt` lists versions checked on a phone-size screen.
  To roll back the page: `git checkout <commit> -- acreage/acreage.html`, then `./release.sh`. Add a line there after each good release.

## Standing rules from zac
- Free tools and data only. No paid subscriptions.
- Never scrape Facebook, Gumtree, Domain or realestate.com.au. Never get around a bot check or a block.
- No keys, passwords or ntfy topics in any file or repo.
- Light theme only, no purple or pink. Plain, simple words.
- Don't waste his usage: no extra runs or polling unless something failed.
