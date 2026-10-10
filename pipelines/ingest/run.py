"""Ingestion runner.

    python -m ingest.run                     # run every source once
    python -m ingest.run --source un-news-africa
    python -m ingest.run --dry-run           # fetch/classify/report, post nothing

Per docs/GOVERNANCE.md every item lands as an unverified claim; skipped items
are logged with the reason so coverage gaps are visible, never silent.
"""
import argparse
import json
import sys

from .classify import classify, match_country
from .connectors import CONNECTORS
from .dedupe import SeenLedger
from .registry import load_registry
from .sink import post_event


def run_source(cfg, pilot_countries, ledger, dry_run: bool) -> dict:
    stats = {"fetched": 0, "posted": 0, "dup": 0, "no_country": 0, "no_type": 0, "error": 0}
    for item in CONNECTORS[cfg.kind](cfg):
        stats["fetched"] += 1
        if ledger.is_seen(item.url, item.title):
            stats["dup"] += 1
            continue
        country = item.country or match_country(f"{item.title} {item.summary}", pilot_countries)
        if not country:
            stats["no_country"] += 1
            print(f"  skip (no pilot country): {item.title[:80]}", file=sys.stderr)
            continue
        event_type = classify(f"{item.title} {item.summary}")
        if not event_type:
            stats["no_type"] += 1
            print(f"  skip (no event type):    {item.title[:80]}", file=sys.stderr)
            continue
        item.country = country
        if dry_run:
            print(f"  would post [{event_type}/{country}]: {item.title[:80]}")
            stats["posted"] += 1
            continue
        try:
            ev = post_event(item, event_type, cfg.confidence)
            ledger.mark(item.url, item.title)
            stats["posted"] += 1
            print(f"  posted {ev['event_id'][:8]} [{event_type}/{country}]: {item.title[:70]}")
        except Exception as exc:  # noqa: BLE001 — one bad item must not kill the run
            stats["error"] += 1
            print(f"  ERROR posting: {exc}", file=sys.stderr)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="run a single source id (default: all)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    registry = load_registry()
    ledger = SeenLedger()
    targets = [registry.get(args.source)] if args.source else registry.sources

    totals: dict[str, int] = {}
    for cfg in targets:
        print(f"[{cfg.id}] ({cfg.kind})")
        stats = run_source(cfg, registry.pilot_countries, ledger, args.dry_run)
        for k, v in stats.items():
            totals[k] = totals.get(k, 0) + v
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
