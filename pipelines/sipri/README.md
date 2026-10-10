# SIPRI arms-transfers connector

Loads the SIPRI Arms Transfers Database trade register into the actor graph
(Neo4j) as `(:Country)-[:SUPPLIED]->(:Country)` edges — documented transfers,
per docs/DATA_MODEL.md "arms and resource routes, where reliable data exists".

## Getting the data (manual export — no scraping)

SIPRI offers no public machine API; the portal is the licensed access path.

1. Go to https://armstransfers.sipri.org (SIPRI Arms Transfers Database).
2. Query the **Trade Register** — e.g. recipients: Sudan, Chad, South Sudan,
   DR Congo, Haiti; all suppliers; year range of interest.
3. Export as CSV and save under `pipelines/data/sipri/` (gitignored).
4. Load: `python -m sipri.run data/sipri/<file>.csv`

Attribution is mandatory and baked into every edge:
"Source: SIPRI Arms Transfers Database". Re-exports replace prior SIPRI edges
(`--wipe-source` default) so the graph mirrors the latest register.

## Data classification

Transfers enter as `observed_fact` (documented deliveries/orders in SIPRI's
register) with `confidence 0.8`; estimate flags on years/numbers lower the
edge's confidence to 0.6. TIV values are SIPRI's trend-indicator values, not
prices — never present them as monetary amounts.
