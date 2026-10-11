"""Publish/update the Human Rights Agent's position from real-time events.

    python -m hra.run           # full: vitals + dev audit + statement + publish
    python -m hra.run --dry-run
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers  # noqa: E402

from .dev_audit import audit_development, draft_statement  # noqa: E402
from .vitals import assess, immune_response  # noqa: E402


def fallback_statement(assessment: dict, actions: list[dict]) -> str:
    lines = ["Position computed from tracked events (deterministic vitals algorithm; statement drafting unavailable)."]
    for c, d in sorted(assessment.items(), key=lambda kv: -kv[1]["pressure"]):
        worst = max(d["vitals"].items(), key=lambda kv: kv[1]["score"])
        lines.append(f"{c}: pressure {d['pressure']:.2f}, most stressed vital: {worst[0]} ({worst[1]['level']}).")
    urgent = [a for a in actions if a["level"] == "urgent"]
    if urgent:
        lines.append(f"{len(urgent)} urgent priority(ies) flagged for human dispatch.")
    return " ".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    resp = httpx.get(f"{API_URL}/events", params={"limit": 1000}, headers=api_headers(), timeout=30)
    resp.raise_for_status()
    events = resp.json()

    assessment = assess(events)
    actions = immune_response(assessment)
    dev_audit = audit_development()
    statement = draft_statement(assessment, actions, dev_audit) or fallback_statement(assessment, actions)

    position = {
        "statement": statement,
        "vitals": assessment,
        "priorities": actions,
        "platform_audit": dev_audit,
        "engine": "hra-vitals-v1" + ("+claude-opus-5" if dev_audit and "error" not in (dev_audit or {}) else ""),
    }
    if args.dry_run:
        print(json.dumps(position, indent=1)[:2500])
        return
    r = httpx.post(f"{API_URL}/hra/position", json=position, headers=api_headers(), timeout=30)
    r.raise_for_status()
    urgent = sum(1 for a in actions if a["level"] == "urgent")
    print(f"position published: {len(assessment)} country(ies), {len(actions)} prioritized action(s), {urgent} urgent (human dispatch)")


if __name__ == "__main__":
    main()
