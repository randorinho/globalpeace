#!/usr/bin/env bash
# Fetch the GeoNames cities15000 gazetteer (CC-BY 4.0) used by
# pipelines/ingest/geolocate.py for city-level event placement.
# ~26k populated places >15k inhabitants; coarse by design — the exposure
# gate allows machine publication of city precision, never exact.
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/pipelines/data/geonames"
mkdir -p "$DEST"
if [[ -s "$DEST/cities15000.txt" ]]; then
  echo "✓ gazetteer already present: $DEST/cities15000.txt"
  exit 0
fi
echo "→ downloading GeoNames cities15000 (CC-BY 4.0, geonames.org)"
curl -sfL https://download.geonames.org/export/dump/cities15000.zip -o "$DEST/cities15000.zip"
unzip -oq "$DEST/cities15000.zip" -d "$DEST"
rm -f "$DEST/cities15000.zip"
wc -l "$DEST/cities15000.txt"
echo "✓ gazetteer installed"
