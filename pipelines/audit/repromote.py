"""Re-evaluate ai_corroborated promotions using current rules + the stored
panel opinions — no new LLM calls. Used after criteria improvements."""
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers  # noqa: E402

from .criteria import corroboration, recency, source_tier  # noqa: E402
from .promotion import promotable  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


def main() -> None:
    evs = httpx.get(f"{API_URL}/events", params={"limit": 1000}, headers=api_headers(), timeout=30).json()
    now = datetime.now(timezone.utc)
    promoted = 0
    for ev in evs:
        if ev["verification_status"] != "unverified" or not ev.get("ai_audit"):
            continue
        tier, _ = source_tier(ev.get("source_urls", []))
        rec, _, _ = recency(ev["date_time"], now)
        corrob = corroboration(ev, evs)
        sig = {"source_tier": tier, "recency": rec, "corroborating_events": corrob}
        if promotable(sig, ev["ai_audit"].get("llm_opinion"), ev):
            r = httpx.post(f"{API_URL}/events/{ev['event_id']}/ai-corroborate",
                           headers=api_headers(), timeout=30)
            if r.status_code == 200:
                promoted += 1
                print(f"promoted: {ev['title'][:70]}")
    print(json.dumps({"promoted": promoted}))


if __name__ == "__main__":
    main()
