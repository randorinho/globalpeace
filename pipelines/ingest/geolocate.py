"""City-level geolocation from a public gazetteer — transparent, offline.

Matches populated-place names (GeoNames cities15000, CC-BY 4.0 — fetch with
scripts/fetch_gazetteer.sh) against item text, scoped to the event's already-
matched country so "Santa Cruz" in a Bolivia story never lands in California.
Longest name wins; ties break on population. Returns CITY precision only —
coarse by design: the exposure gate (audit/promotion.py) allows machine
publication of city placement, never exact coordinates.

Degrades gracefully: no gazetteer file -> no locations, logged once.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

GAZETTEER = Path(__file__).parent.parent / "data" / "geonames" / "cities15000.txt"

# country ISO2 -> list of (name_lower, lat, lon, population)
_INDEX: dict[str, list[tuple[str, float, float, int]]] | None = None
_WARNED = False


def _load() -> dict[str, list[tuple[str, float, float, int]]]:
    global _INDEX, _WARNED
    if _INDEX is not None:
        return _INDEX
    _INDEX = {}
    if not GAZETTEER.exists():
        if not _WARNED:
            print("geolocate: gazetteer missing — run scripts/fetch_gazetteer.sh "
                  "(events will carry no location)", file=sys.stderr)
            _WARNED = True
        return _INDEX
    with GAZETTEER.open(encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 15:
                continue
            name, asciiname, lat, lon, cc, pop = f[1], f[2], f[4], f[5], f[8], f[14]
            try:
                entry_pop = int(pop or 0)
                entries = _INDEX.setdefault(cc.upper(), [])
                for n in {name.lower(), asciiname.lower()}:
                    if len(n) >= 4:  # 3-letter names ("Uba") are false-positive magnets
                        entries.append((n, float(lat), float(lon), entry_pop))
            except ValueError:
                continue
    return _INDEX


def locate(text: str, country_iso2: str) -> tuple[float, float] | None:
    """Coordinates of the most specific city named in the text, within the
    given country — or None. City precision only."""
    entries = _load().get(country_iso2.upper())
    if not entries:
        return None
    lowered = text.lower()
    best: tuple[int, int, float, float] | None = None  # (name_len, pop, lat, lon)
    for name, lat, lon, pop in entries:
        if name in lowered and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", lowered):
            key = (len(name), pop, lat, lon)
            if best is None or key[:2] > best[:2]:
                best = key
    return (best[2], best[3]) if best else None
