"""Situation clustering: the unit a peace approach attaches to.

Deterministic: treated events (human-reviewed or machine-corroborated) are
grouped per country over a rolling window, enriched with the latest HRA
vitals and priorities. Untreated claims never feed the solutions engine —
suggestions must stand on the platform's best-verified ground.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

TREATED = ("verified", "partially_verified", "ai_corroborated")
WINDOW_DAYS = 30


def build_situations(events: list[dict], hra_position: dict | None) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    vitals = (hra_position or {}).get("vitals", {})
    priorities = (hra_position or {}).get("priorities", [])

    by_country: dict[str, list[dict]] = {}
    for ev in events:
        if ev.get("verification_status") not in TREATED:
            continue
        dt = datetime.fromisoformat(ev["date_time"].replace("Z", "+00:00"))
        if dt < cutoff:
            continue
        by_country.setdefault(ev["country"], []).append(ev)

    situations = []
    for country, evs in by_country.items():
        situations.append({
            "country": country,
            "window_days": WINDOW_DAYS,
            "events": [
                {
                    "event_id": e["event_id"],
                    "title": e.get("title"),
                    "event_type": e.get("event_type"),
                    "date": e["date_time"][:10],
                    "status": e["verification_status"],
                }
                for e in sorted(evs, key=lambda x: x["date_time"], reverse=True)[:20]
            ],
            "vitals": vitals.get(country, {}),
            "hra_priorities": [p for p in priorities if p.get("country") == country],
        })
    # most pressured situations first
    situations.sort(key=lambda s: -(s["vitals"].get("pressure") or 0))
    return situations
