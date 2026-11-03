"""Run the solutions engine: treated events + HRA vitals -> concrete
political and economic approaches per situation, published for review.

    python -m solutions.run           # draft + publish
    python -m solutions.run --dry-run
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers  # noqa: E402

import llm_budget  # noqa: E402

from .engine import draft_approaches  # noqa: E402
from .situations import build_situations  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    events = httpx.get(f"{API_URL}/events", params={"limit": 1000},
                       headers=api_headers(), timeout=30).json()
    hra = httpx.get(f"{API_URL}/public/hra/position", timeout=30).json()

    situations = build_situations(events, hra)
    print(f"{len(situations)} situation(s) from treated events", file=sys.stderr)

    if not args.dry_run and not llm_budget.throttle(
            "solutions_run", llm_budget.interval_h("GPAI_SOLUTIONS_INTERVAL_H", 24.0)):
        print("solutions: outside daily AI window — skipped", file=sys.stderr)
        return

    published = 0
    for situation in situations:
        # redraft only when the situation's event set changed since last publish
        fp = ",".join(sorted(e["event_id"] for e in situation["events"]))
        if not args.dry_run and llm_budget.unchanged(f"solutions:{situation['country']}", fp):
            print(f"[{situation['country']}] unchanged event set — redraft skipped", file=sys.stderr)
            continue
        drafted = draft_approaches(situation)
        if not drafted:
            print(f"[{situation['country']}] engine unavailable — skipped", file=sys.stderr)
            continue
        payload = {
            "country": situation["country"],
            "window_days": situation["window_days"],
            "situation": situation,
            "approaches": drafted["approaches"],
            "engine": f"solutions-v1+{drafted['model']}",
        }
        if args.dry_run:
            print(json.dumps(payload, indent=1)[:1500])
            continue
        r = httpx.post(f"{API_URL}/solutions", json=payload,
                       headers=api_headers(), timeout=30)
        r.raise_for_status()
        llm_budget.record(f"solutions:{situation['country']}", fp)
        published += 1
        pol = sum(1 for a in drafted["approaches"] if a["level"] == "political")
        eco = sum(1 for a in drafted["approaches"] if a["level"] == "economic")
        print(f"[{situation['country']}] published: {pol} political + {eco} economic approach(es)")
    print(f"done: {published} situation solution set(s) published")


if __name__ == "__main__":
    main()
