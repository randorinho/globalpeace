"""Contributions drain — dark-origin phase 2 (docs/DARK_ORIGIN.md).

Public submissions land in a D1 buffer at the edge (edge/gateway); this stage
pulls them into the origin's moderation queue. Strictly outbound: the origin
calls the worker, never the reverse.

    python -m contributions.run            # drain once
    python -m contributions.run --dry-run  # list pending, change nothing

Flow: GET pending rows from the edge (gateway-secret auth) → POST them to the
origin's /contributions/import (canonical PII screen + referential check; the
edge row id is the contribution_id, so retries after a failed ack are no-ops)
→ ack every terminal id at the edge. An unreachable edge or an edge that does
not know the internal routes yet logs and exits 0 — the pipeline must not fail
while the worker deploy is pending.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers, gateway_secret  # noqa: E402

EDGE_URL = os.environ.get("GPAI_EDGE_URL", "https://globalpeace.ai")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    secret = gateway_secret()
    if not secret:
        print("→ drain skipped: no gateway secret configured")
        return
    edge_headers = {"x-gateway-secret": secret}

    try:
        resp = httpx.get(f"{EDGE_URL}/api/internal/contributions/pending",
                         headers=edge_headers, timeout=30)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 — edge down/undeployed must not fail the pipeline
        print(f"→ drain skipped: edge unreachable ({exc})")
        return
    pending = resp.json().get("contributions", [])
    if not pending:
        print(json.dumps({"pending": 0, "imported": 0, "skipped": 0, "acked": 0}))
        return
    if args.dry_run:
        for row in pending:
            print(f"  would import {row['id']}: {row['text'][:70]}")
        print(json.dumps({"pending": len(pending)}))
        return

    imp = httpx.post(f"{API_URL}/contributions/import",
                     json={"contributions": pending}, headers=api_headers(), timeout=60)
    imp.raise_for_status()
    result = imp.json()
    terminal = result["imported"] + [s["id"] for s in result["skipped"]]
    for note in result.get("notes", []):
        print(f"  note {note['id']}: {note['note']}", file=sys.stderr)
    for s in result["skipped"]:
        print(f"  skipped {s['id']}: {s['reason']}", file=sys.stderr)

    acked = 0
    if terminal:
        ack = httpx.post(f"{EDGE_URL}/api/internal/contributions/ack",
                         json={"ids": terminal}, headers=edge_headers, timeout=30)
        ack.raise_for_status()
        acked = ack.json().get("acked", 0)
    print(json.dumps({"pending": len(pending), "imported": len(result["imported"]),
                      "skipped": len(result["skipped"]), "acked": acked}))


if __name__ == "__main__":
    main()
