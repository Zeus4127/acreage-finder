#!/bin/bash
# Copy the checked site to the public website branch (gh-pages) of the acreage-finder repo and push it.
# Run only after release.sh printed RELEASE PASSED. GitHub Pages serves the branch at
#   https://zeus4127.github.io/acreage-finder/
# Never point this at bargain-finder: that repo serves the caravan Bargain Finder website.
set -eu
cd "$(dirname "$0")"
REPO="$(cd .. && pwd)"; WT="$REPO/../acreage-site-gh-pages"
case "$(git -C "$REPO" remote get-url origin)" in *acreage-finder*) ;; *) echo "SITE: origin is not acreage-finder; refusing to publish"; exit 1;; esac
if [ ! -e "$WT/.git" ]; then
  git -C "$REPO" worktree prune
  if git -C "$REPO" ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
    git -C "$REPO" fetch -q --depth 1 origin gh-pages:gh-pages && git -C "$REPO" worktree add -f "$WT" gh-pages
  else
    git -C "$REPO" worktree add -f --detach "$WT" && git -C "$WT" checkout -q --orphan gh-pages && { git -C "$WT" rm -rq --cached . 2>/dev/null || true; }
    find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  fi
fi
cp acreage.html "$WT/index.html"; cp acreage-data.js history-data.js aus-map.js alerts-feed.json "$WT/"; mkdir -p "$WT/media" && cp media/*.jpg media/CREDITS.md "$WT/media/"
touch "$WT/.nojekyll"
cd "$WT"
git add -A
if git diff --cached --quiet; then echo "SITE: nothing new"; exit 0; fi
git commit -qm "Site update $(date -u +%Y-%m-%dT%H:%M)Z (release checks passed)"
for i in 1 2 3 4; do git push -q -u origin gh-pages && { echo "SITE PUBLISHED: https://zeus4127.github.io/acreage-finder/"; exit 0; }; sleep $((i*3)); done
echo "SITE: push failed"; exit 1
