"""Human ratification/demotion of a vetted source — always logged.

    python -m vetting.ratify <domain> --by <operator-identity>
    python -m vetting.ratify <domain> --by <operator-identity> --demote watch --reason "..."
"""
import argparse
import sys
from pathlib import Path

import yaml

from .run import AUDIT_LOG, REGISTRY, log_entry  # noqa: F401 (AUDIT_LOG re-exported for tooling)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--by", required=True, help="human operator identity")
    ap.add_argument("--demote", choices=["watch", "rejected"], default=None)
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    reg = yaml.safe_load(REGISTRY.read_text())
    entry = reg["sources"].get(args.domain)
    if not entry:
        sys.exit(f"{args.domain} not in registry — vet it first (python -m vetting.run <url>)")

    if args.demote:
        entry["tier"], entry["status"] = args.demote, "ratified"
        action = f"demoted_to_{args.demote}"
    else:
        if entry.get("tier") != "vetted":
            sys.exit(f"{args.domain} tier is '{entry.get('tier')}' — only vetted sources can be ratified")
        entry["status"] = "ratified"
        action = "ratified"

    at = log_entry("human_decision", {
        "domain": args.domain, "action": action, "actor": args.by,
        "reason": args.reason or "panel vetting reviewed and accepted",
        "prior": {k: entry.get(k) for k in ("tier", "vetted_at", "by")},
    })
    entry["ratified_by"], entry["ratified_at"] = args.by, at
    REGISTRY.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    print(f"{args.domain}: {action} by {args.by} at {at} (logged)")


if __name__ == "__main__":
    main()
