"""UCDP GED (Georeferenced Event Dataset) API connector.

Access requires a registered token (https://ucdp.uu.se/apidocs/): set
UCDP_API_TOKEN (infra/.env), sent as the x-ucdp-access-token header.
Quota is 5,000 requests/day and EVERY page counts (errors included), so
pages are maxed out (pagesize 1000) and each dataset release is walked
exactly once: GED releases are immutable snapshots (annual "26.1" covers
through 2025; monthly candidate releases use the same API shape), so after
a complete walk a `(version, since)` marker in .state/ skips the source
entirely until `ucdp_version`/`since` change in sources.yaml. Delete
`.state/ucdp-<source id>.done` to force a re-walk — the seen-ledger and the
origin's unique-source-URL index make re-walks idempotent.

Events arrive with structured country, type and coordinates, so the regex
classifier and gazetteer are bypassed. Coordinates are forwarded only for
where_prec 1-2 (settlement-level) — admin/country centroids (prec >= 3)
would be false precision, and the exposure gate publishes city placement,
never exact coordinates.
"""
import os
import sys
from datetime import datetime

import httpx

from ..countries import match_country
from ..dedupe import STATE_DIR
from ..items import RawItem
from ..registry import SourceConfig

API = "https://ucdpapi.pcr.uu.se/api/gedevents"
PAGESIZE = 1000
MAX_PAGES = 60  # per-run request cap; a truncated walk logs, stays unmarked, retries next run

VIOLENCE = {1: "State-based violence", 2: "Non-state violence", 3: "One-sided violence"}


def fetch_ucdp(cfg: SourceConfig) -> list[RawItem]:
    token = os.environ.get("UCDP_API_TOKEN", "")
    if not token:
        raise RuntimeError("set UCDP_API_TOKEN (registered token) to use the UCDP API")
    version = cfg.ucdp_version or "26.1"
    stamp = f"{version}|{cfg.since or ''}"
    marker = STATE_DIR / f"ucdp-{cfg.id}.done"
    if marker.exists() and marker.read_text().strip() == stamp:
        print(f"  release {version} already walked — skipping (request quota)", file=sys.stderr)
        return []

    headers = {"x-ucdp-access-token": token}
    params: dict | None = {"pagesize": PAGESIZE}
    if cfg.since:
        params["StartDate"] = cfg.since
    next_url: str | None = f"{API}/{version}"
    items: list[RawItem] = []
    pages = 0
    while next_url and pages < MAX_PAGES:
        resp = httpx.get(next_url, params=params, headers=headers, timeout=60)
        params = None  # NextPageUrl already carries the query string
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("Result") or []
        if not rows:
            next_url = None
            break
        items.extend(_to_item(cfg, version, row) for row in rows)
        pages += 1
        next_url = data.get("NextPageUrl") or None
    if next_url:
        print(f"  page cap hit ({MAX_PAGES}) — walk incomplete, will resume next run", file=sys.stderr)
    elif not os.environ.get("GPAI_INGEST_DRY_RUN"):  # a dry run must not block the real walk
        STATE_DIR.mkdir(exist_ok=True)
        marker.write_text(stamp)
    return items


def _to_item(cfg: SourceConfig, version: str, row: dict) -> RawItem:
    country_name = row.get("country") or ""
    best = row.get("best", 0)
    place = row.get("where_coordinates") or row.get("adm_1") or ""
    where = f"{place}, {country_name}" if place else country_name
    kind = VIOLENCE.get(row.get("type_of_violence"), "Armed violence")
    location = None
    if row.get("where_prec") in (1, 2) and row.get("latitude") is not None:
        location = (float(row["latitude"]), float(row["longitude"]))
    return RawItem(
        source_id=cfg.id,
        title=f"{kind}: {row.get('side_a')} – {row.get('side_b')}, {best} killed ({where})",
        url=f"{API}/{version}?id={row['id']}",
        published=datetime.fromisoformat(row["date_start"]),
        summary=row.get("where_description") or "",
        country=match_country(country_name),  # None falls back to run.py's title match + logged skip
        event_type="attack",
        location=location,
        extra={
            "relid": row.get("relid"),
            "type_of_violence": row.get("type_of_violence"),
            "deaths_civilians": row.get("deaths_civilians"),
            "deaths_low": row.get("low"),
            "deaths_high": row.get("high"),
            "where_prec": row.get("where_prec"),
            "date_end": row.get("date_end"),
        },
    )
