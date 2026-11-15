#!/usr/bin/env bash
# Daily refresh: new sold listings (Farmbuy, Farm Property), then all 10+ acre listings (Farmbuy and Farm Property), then the one-file page.
set -e
cd "$(dirname "$0")"
python3 -I -u scan_sold.py
python3 -I -u scan_fp_sold.py || echo "Farm Property sold step failed; carrying on"
python3 -I -u scan_fp_sale.py || echo "Farm Property for-sale step failed; carrying on"
if [ "$(date +%u)" = 1 ] || [ ! -f nsw-sales.json ]; then  # Mondays, or when missing: refresh NSW government sales (about 45 minutes)
  rm -f nsw-vg/rural-sales.json nsw-vg/semi-rural-sales.json
  python3 -I -u fetch_nsw_map.py && python3 -I -u fetch_nsw_map.py semi && python3 -I -u import_nsw_vg.py \
    && python3 -I -u build_centroids.py || echo "NSW sales step failed; carrying on"
fi
python3 -I -u build_listed.py || echo "Listed dates step failed; carrying on"
python3 -I -u scan_acreage.py
python3 -I -u lga_lookup.py || echo "Council lookup failed; carrying on"   # council for blocks without one (ABS map), used by the rescore below
python3 -I -u scan_catches.py && python3 -I -u scan_acreage.py --rescore || echo "Catch checks failed; carrying on"
if [ "$(date +%u)" = 1 ]; then  # Mondays: re-test the prices against real sales and re-learn the asking-to-sale gap
  python3 -I -u backtest.py --tune && python3 -I -u scan_acreage.py --rescore || echo "Backtest step failed; carrying on"
  python3 -I -u growth_check.py && python3 -I -u growth_check_states.py && python3 -I -u growth_check_qld.py && python3 -I -u growth_jumps.py && python3 -I -u pop_forecast.py || echo "Growth check failed; carrying on"   # re-check the Growth score: NSW sales, all-state councils, QLD valuations
fi
python3 -I -u elevation.py || echo "Elevation step failed; carrying on"
python3 -I -u water_check.py || echo "Creek check step failed; carrying on"
python3 -I -u qld_planning.py 300 || echo "QLD planning step failed; carrying on"   # QLD planning areas, growth fronts and big projects (new blocks only)
python3 -I -u edge_check.py 400 || echo "Town-edge check failed; carrying on"   # NSW and VIC zoning within 2 km (new blocks only)
python3 -I -u sa_planning.py 200 || echo "SA planning step failed; carrying on"   # SA zones, rezonings and greenfield land (new blocks only)
python3 -I -u wa_planning.py 200 || echo "WA planning step failed; carrying on"   # WA region scheme: Urban Deferred, rezonings, planned estates (new blocks only)
python3 -I -u drive_times.py || echo "Drive times step failed; carrying on"
python3 -I -u growth.py || echo "Growth score step failed; carrying on"
python3 -I -u pulse.py || echo "Market pulse step failed; carrying on"
python3 -I -u alerts.py || echo "Alerts step failed; carrying on"
python3 -I build_page.py "${1:-acreage-finder.html}"
