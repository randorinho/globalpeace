"""AI audit runner.

    python -m audit.run                # transparent rules only
    python -m audit.run --with-desks   # + continental desks: 6 analyst agents per continent
    python -m audit.run --panel-size 3 # fewer panelists per desk (cost control)
    python -m audit.run --dry-run      # compute, print, post nothing
"""
import argparse
import json
import os
import sys

import httpx

from .continents import group_by_desk
from .criteria import audit_event
from .desks import run_panel

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent.parent))
from common import api_headers  # noqa: E402

API_URL = os.environ.get("GPAI_API_URL", "http://localhost:8000")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-desks", action="store_true",
                    help="deploy the continental analyst panels (6 agents per desk)")
    ap.add_argument("--panel-size", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    resp = httpx.get(f"{API_URL}/events", params={"limit": 1000}, timeout=30, headers=api_headers())
    resp.raise_for_status()
    all_events = resp.json()
    targets = [e for e in all_events if e.get("ai_audit") is None]
    print(f"{len(targets)} unaudited event(s)", file=sys.stderr)

    # 1. transparent rules for every event
    audits: dict[str, dict] = {}
    for ev in targets:
        audits[ev["event_id"]] = audit_event(ev, all_events)
        ev["_rules_audit"] = audits[ev["event_id"]]

    # 2. continental desks: one panel of analyst agents per continent with work
    if args.with_desks and targets:
        for desk, desk_events in sorted(group_by_desk(targets).items()):
            print(f"[desk:{desk}] digest of {len(desk_events)} event(s), "
                  f"deploying {args.panel_size} analysts", file=sys.stderr)
            panel = run_panel(desk, desk_events, args.panel_size)
            if panel is None:
                print(f"[desk:{desk}] LLM layer unavailable — rules only", file=sys.stderr)
                continue
            for ev in desk_events:
                res = panel.get(ev["event_id"])
                audit = audits[ev["event_id"]]
                audit["engine"] += f"+desk:{desk}x{panel['_panelists_ran']}"
                audit["llm_opinion"] = {
                    "desk": desk, "panelists": panel["_panelists_ran"],
                    "concerns": res["concerns"] if res else [],
                    "consensus_count": res["consensus_count"] if res else 0,
                    "digest_notes": panel["_digest_notes"],
                    "model": "claude-opus-5",
                }
                if res and res["concerns"]:
                    audit["reasons"] += res["concerns"]
                    if audit["verdict"] == "credible_recent":
                        audit["verdict"] = "needs_additional_verification"  # doubt only downgrades

    def promotable(ev: dict, audit: dict) -> bool:
        """ai_corroborated criteria: institutional source, independently
        corroborated, fresh/recent, and — when a desk panel ran — zero
        consensus-level objections. Pending cross-checks remain visible as
        caveats; promotion never implies human verification."""
        sig = audit["signals"]
        if sig["source_tier"] != "institutional" or sig["recency"] == "stale":
            return False
        if sig["corroborating_events"] < 1:
            return False
        # Fail-closed (HRA self-audit finding): if the analyst panel did not
        # actually run, machine corroboration is withheld, not granted.
        op = audit.get("llm_opinion")
        if not op or not op.get("panelists") or op.get("consensus_count", 0) > 0:
            return False
        # Exposure gate (HRA self-audit finding): named actors or exact
        # coordinates raise targeting risk — publication of those needs a human.
        if ev.get("actors") or ev.get("location") is not None:
            return False
        return ev.get("verification_status") == "unverified"

    counts: dict[str, int] = {}
    promoted = 0
    for ev in targets:
        audit = audits[ev["event_id"]]
        counts[audit["verdict"]] = counts.get(audit["verdict"], 0) + 1
        label = f"[{audit['verdict']}] {ev['title'][:60] or ev['event_id'][:8]}"
        if args.dry_run:
            print(label)
            continue
        r = httpx.post(f"{API_URL}/events/{ev['event_id']}/audit", json=audit, timeout=30, headers=api_headers())
        r.raise_for_status()
        if promotable(ev, audit):
            pr = httpx.post(f"{API_URL}/events/{ev['event_id']}/ai-corroborate", timeout=30, headers=api_headers())
            if pr.status_code == 200:
                promoted += 1
                label += " -> ai_corroborated"
        print(label)
    counts["promoted_ai_corroborated"] = promoted
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
