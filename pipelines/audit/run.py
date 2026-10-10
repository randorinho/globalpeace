"""AI audit runner.

    python -m audit.run                # audit all unaudited events
    python -m audit.run --with-llm     # add the Claude analyst's second opinion
    python -m audit.run --dry-run      # compute, print, post nothing
"""
import argparse
import json
import os
import sys

import httpx

from .criteria import audit_event
from .llm import llm_opinion

API_URL = os.environ.get("GPAI_API_URL", "http://localhost:8000")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-llm", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    resp = httpx.get(f"{API_URL}/events", params={"limit": 1000}, timeout=30)
    resp.raise_for_status()
    all_events = resp.json()
    targets = [e for e in all_events if e.get("ai_audit") is None]
    print(f"{len(targets)} unaudited event(s)", file=sys.stderr)

    counts: dict[str, int] = {}
    for ev in targets:
        audit = audit_event(ev, all_events)
        if args.with_llm:
            opinion = llm_opinion(ev, audit)
            if opinion:
                audit["llm_opinion"] = opinion
                audit["engine"] += "+claude-opus-5"
                if opinion.get("additional_concerns"):
                    audit["reasons"] += [f"analyst: {c}" for c in opinion["additional_concerns"]]
                    if audit["verdict"] == "credible_recent":
                        audit["verdict"] = "needs_additional_verification"  # doubt only ever downgrades
        counts[audit["verdict"]] = counts.get(audit["verdict"], 0) + 1
        label = f"[{audit['verdict']}] {ev['title'][:60] or ev['event_id'][:8]}"
        if args.dry_run:
            print(label)
            continue
        r = httpx.post(f"{API_URL}/events/{ev['event_id']}/audit", json=audit, timeout=30)
        r.raise_for_status()
        print(label)
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
