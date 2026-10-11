"""Vet a candidate source and record the outcome in the trust registry.

    python -m vetting.run https://example-outlet.org/feed.xml
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .analyzer import vet

REGISTRY = Path(__file__).parent / "registry.yaml"
AUDIT_LOG = Path(__file__).parent / "audit_log.jsonl"  # append-only, git-versioned


def log_entry(kind: str, payload: dict) -> str:
    """Append an auditable record (AI-Act-style logging: who/what/when,
    externally inspectable via the public repository history)."""
    entry = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        **payload,
    }
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["at"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()

    try:
        result = vet(args.url)
    except Exception as exc:
        # A source we cannot even sample cannot be vetted — and we do not
        # evade bot protection. It stays un-trusted (watch) with the reason.
        import httpx
        if isinstance(exc, httpx.HTTPError):
            print(json.dumps({"domain": args.url, "verdict": "watch",
                              "reason": f"unreachable for sampling ({exc}) — not vetted, not trusted"}, indent=1))
            return
        raise
    reg = yaml.safe_load(REGISTRY.read_text())
    entry = reg["sources"].get(result["domain"], {})
    if entry.get("tier") == "institutional":
        print(f"{result['domain']} is curated institutional — registry unchanged", file=sys.stderr)
    else:
        logged_at = log_entry("vetting_panel", {
            "domain": result["domain"], "url": args.url, "verdict": result["verdict"],
            "unanimous": result["unanimous"], "opinions": result["opinions"],
            "model": result["model"], "actor": "vetting-panel(claude-opus-5 x3)",
        })
        reg["sources"][result["domain"]] = {
            "tier": result["verdict"] if result["verdict"] != "rejected" else "rejected",
            "status": "provisional",
            "vetted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "by": "vetting-panel(claude-opus-5 x3)",
            "notes": "; ".join(
                i for o in result["opinions"].values() for i in o["fake_news_indicators"]
            )[:300] or "no fake-news indicators raised",
            "audit_log_ref": logged_at,
        }
        REGISTRY.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    print(json.dumps({k: result[k] for k in ("domain", "verdict", "unanimous")}, indent=1))
    for lens, o in result["opinions"].items():
        print(f"[{lens}] {o['recommendation']} / risk {o['manipulation_risk']}: {o['rationale'][:140]}")


if __name__ == "__main__":
    main()
