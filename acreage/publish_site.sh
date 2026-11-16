#!/bin/bash
# Copy the checked site to the public website branch (gh-pages) of this repo and push it.
# Run only after release.sh printed RELEASE PASSED. GitHub Pages serves the branch at
#   https://zeus4127.github.io/bargain-finder/
set -eu
cd "$(dirname "$0")"
REPO="$(cd .. && pwd)"; WT="$REPO/../site-gh-pages"
if [ ! -d "$WT/.git" ] && [ ! -f "$WT/.git" ]; then
  if git -C "$REPO" ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
    git -C "$REPO" fetch -q origin gh-pages && git -C "$REPO" worktree add -f "$WT" gh-pages
  else
    git -C "$REPO" worktree add -f --detach "$WT" && git -C "$WT" checkout -q --orphan gh-pages && git -C "$WT" rm -rq --cached . 2>/dev/null || true
    find "$WT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  fi
fi
cp acreage.html "$WT/index.html"; cp acreage-data.js history-data.js alerts-feed.json "$WT/"
touch "$WT/.nojekyll"
cat > "$WT/robots.txt" <<'R'
User-agent: *
Disallow: /
R
cd "$WT"
git add -A
if git diff --cached --quiet; then echo "SITE: nothing new"; exit 0; fi
git commit -qm "Site update $(date -u +%Y-%m-%dT%H:%M)Z (release checks passed)"
for i in 1 2 3 4; do git push -q -u origin gh-pages && { echo "SITE PUBLISHED: https://zeus4127.github.io/bargain-finder/"; exit 0; }; sleep $((i*3)); done
echo "SITE: push failed"; exit 1
