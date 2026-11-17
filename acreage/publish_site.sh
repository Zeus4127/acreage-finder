#!/bin/bash
# Copy the checked Acreage Finder site to its OWN public website repo and push it.
# Run only after release.sh printed RELEASE PASSED.
#
# IMPORTANT: this repo (bargain-finder) already serves the caravan Bargain Finder website from its main
# branch with GitHub Pages. Never switch this repo's Pages setting and never publish Acreage Finder here.
# Acreage Finder needs its own repo (for example Zeus4127/acreage-finder with Pages on main).
# To turn publishing on, put that repo's address on one line in acreage/site-repo.txt, e.g.
#   https://github.com/Zeus4127/acreage-finder
set -eu
cd "$(dirname "$0")"
[ -s site-repo.txt ] || { echo "SITE: no public site repo set (see publish_site.sh); skipped"; exit 0; }
URL="$(head -1 site-repo.txt | tr -d '[:space:]')"
case "$URL" in *bargain-finder*) echo "SITE: refusing to publish into bargain-finder (it hosts the caravan site)"; exit 1;; esac
WT="$(cd ../.. && pwd)/acreage-site-public"
[ -d "$WT/.git" ] || git clone -q --depth 1 "$URL" "$WT" || { echo "SITE: can't reach $URL"; exit 1; }
cp acreage.html "$WT/index.html"; cp acreage-data.js history-data.js aus-map.js alerts-feed.json "$WT/"
mkdir -p "$WT/media" && cp media/*.jpg media/CREDITS.md "$WT/media/"
touch "$WT/.nojekyll"
cd "$WT"
git add -A
if git diff --cached --quiet; then echo "SITE: nothing new"; exit 0; fi
git commit -qm "Site update $(date -u +%Y-%m-%dT%H:%M)Z (release checks passed)"
for i in 1 2 3 4; do git push -q origin HEAD && { echo "SITE PUBLISHED"; exit 0; }; sleep $((i*3)); done
echo "SITE: push failed"; exit 1
