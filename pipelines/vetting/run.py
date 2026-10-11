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
        reg["sources"][result["domain"]] = {
            "tier": result["verdict"] if result["verdict"] != "rejected" else "rejected",
            "status": "provisional",
            "vetted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "by": "vetting-panel(claude-opus-5 x3)",
            "notes": "; ".join(
                i for o in result["opinions"].values() for i in o["fake_news_indicators"]
            )[:300] or "no fake-news indicators raised",
        }
        REGISTRY.write_text(yaml.safe_dump(reg, sort_keys=False, allow_unicode=True))
    print(json.dumps({k: result[k] for k in ("domain", "verdict", "unanimous")}, indent=1))
    for lens, o in result["opinions"].items():
        print(f"[{lens}] {o['recommendation']} / risk {o['manipulation_risk']}: {o['rationale'][:140]}")


if __name__ == "__main__":
    main()
