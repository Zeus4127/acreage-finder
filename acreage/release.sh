#!/bin/bash
# Build the page and only release it if every check passes. A failed build never replaces the last good one.
#   ./release.sh /path/acreage-finder.html     (the file to publish; the last good copy is kept next to it as *.good.html)
# Prints RELEASE PASSED (publish OUT) or RELEASE FAILED (publish nothing; the last good page stays live).
set -u
cd "$(dirname "$0")"
OUT="${1:-acreage-finder.html}"; TRY="${OUT%.html}.try.html"; GOOD="${OUT%.html}.good.html"
python3 -I build_page.py "$TRY" || { echo "RELEASE FAILED: page build"; exit 1; }
if python3 -I checks/check_data.py && node checks/check_page.js "$TRY"; then
  python3 -I checks/check_data.py --accept >/dev/null
  cp "$TRY" "$OUT"; cp "$TRY" "$GOOD"; rm -f "$TRY"
  echo "RELEASE PASSED: $OUT is ready to publish"
else
  rm -f "$TRY"; [ -f "$GOOD" ] && cp "$GOOD" "$OUT"
  echo "RELEASE FAILED: not publishing; $OUT is still the last good version"; exit 1
fi
