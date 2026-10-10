"""SIPRI connector CLI.

    python -m sipri.run data/sipri/trade-register.csv
    python -m sipri.run tests/fixture_trade_register.csv --fixture   # synthetic smoke test
"""
import argparse
import sys
from pathlib import Path

from .graph import load
from .loader import parse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--fixture", action="store_true",
                    help="load as source FIXTURE (synthetic test data, wiped separately)")
    ap.add_argument("--keep", action="store_true", help="do not wipe prior edges of this source")
    args = ap.parse_args()

    transfers = parse(args.csv.read_text(encoding="utf-8-sig"))
    print(f"parsed {len(transfers)} transfer(s) from {args.csv.name}", file=sys.stderr)
    source = "FIXTURE" if args.fixture else "SIPRI Arms Transfers Database"
    n = load(transfers, source=source, wipe_source=not args.keep)
    print(f"graph now holds {n} edge(s) for source '{source}'")


if __name__ == "__main__":
    main()
