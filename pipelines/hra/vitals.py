"""The immune system: an independent, deterministic algorithm scoring each
country's vital systems from tracked events in real time.

Independent means: it has its own criteria (this file), it reads events but
cannot change verification statuses, and its output is published without
operator pre-approval — within the platform's publication rules (no personal
data, no exact-location inference, no country rankings: vitals are per-country
absolute conditions, never a league table).

Trust weighting mirrors the verification ladder; recency decays on a 14-day
half-life so the position tracks events as they move.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone

STATUS_WEIGHT = {
    "verified": 1.0,
    "partially_verified": 0.8,
    "ai_corroborated": 0.6,
    "unverified": 0.25,
    "disputed": 0.1,
    "retracted": 0.0,
}

VITALS = ("civilian_safety", "population_stability", "food_security",
          "health_system", "humanitarian_access")

FOOD_RE = re.compile(r"famine|food insecur|lean season|soudure|harvest|r[ée]colte|hunger|prix|price", re.I)
HEALTH_RE = re.compile(r"cholera|measles|epidemic|health|malnutrition|hospital|clinic", re.I)
ACCESS_RE = re.compile(r"access|obstruct|blockad|convoy|corridor|denial|siege", re.I)

THRESHOLDS = (("alarm", 0.66), ("concern", 0.33), ("watch", 0.0))

# The preventive playbook (docs/ARCHITECTURE.md) keyed by vital. The agent
# prioritizes; humans dispatch anything urgent.
PLAYBOOK = {
    "civilian_safety": "Activate civilian-protection channels; request independent verification of attack reports; alert protection clusters.",
    "population_stability": "Engage UNHCR/IOM coordination on displacement response; prepare reception-capacity support for receiving areas.",
    "food_security": "Escalate to food-security clusters (WFP/FEWS NET/Cadre Harmonisé actors); support independent market monitoring.",
    "health_system": "Alert WHO country office and health cluster; support surveillance verification and supply corridors.",
    "humanitarian_access": "Prioritize access negotiations through established mediators; document obstructions for humanitarian diplomacy.",
}


def _impact(ev: dict) -> float:
    total = sum(v for v in (ev.get("civilian_impact") or {}).values() if isinstance(v, (int, float)))
    return min(2.0, 1.0 + math.sqrt(total) / 10)


def _decay(ev: dict, now: datetime) -> float:
    dt = datetime.fromisoformat(ev["date_time"].replace("Z", "+00:00"))
    days = max(0.0, (now - dt).total_seconds() / 86400)
    return math.exp(-days / 14)


def _vitals_for(ev: dict) -> list[str]:
    text = ev.get("title") or ""
    hit = []
    if ev.get("event_type") == "attack":
        hit.append("civilian_safety")
    if ev.get("event_type") == "displacement":
        hit.append("population_stability")
    if FOOD_RE.search(text):
        hit.append("food_security")
    if HEALTH_RE.search(text):
        hit.append("health_system")
    if ACCESS_RE.search(text):
        hit.append("humanitarian_access")
    return hit or ["civilian_safety"] if ev.get("event_type") == "attack" else hit


def assess(events: list[dict], now: datetime | None = None) -> dict:
    """Returns {country: {vitals: {name: {score, level, events}}, pressure}}."""
    now = now or datetime.now(timezone.utc)
    by_country: dict[str, dict] = {}
    for ev in events:
        weight = STATUS_WEIGHT.get(ev.get("verification_status", "unverified"), 0.2)
        if weight == 0:
            continue
        signal = weight * _decay(ev, now) * _impact(ev)
        c = by_country.setdefault(ev["country"], {v: {"score": 0.0, "events": []} for v in VITALS})
        for vital in _vitals_for(ev):
            c[vital]["score"] += signal
            c[vital]["events"].append(ev["event_id"])

    result: dict[str, dict] = {}
    for country, vitals in by_country.items():
        out, pressure = {}, 0.0
        for name, data in vitals.items():
            # squash accumulated signal into 0..1 (3+ strong recent reports ≈ alarm)
            score = round(1 - math.exp(-data["score"] / 2.0), 3)
            level = next(lvl for lvl, cut in THRESHOLDS if score >= cut)
            out[name] = {"score": score, "level": level, "evidence_events": data["events"][:10]}
            pressure = max(pressure, score)
        result[country] = {"vitals": out, "pressure": round(pressure, 3)}
    return result


def immune_response(assessment: dict) -> list[dict]:
    """Prioritized diplomatic actions, highest pressure first — immediately
    computed, never automatically dispatched: urgent items carry an explicit
    human-dispatch requirement (docs/GOVERNANCE.md, APDSI Art. 86-C)."""
    actions: list[dict] = []
    for country, data in assessment.items():
        for vital, v in data["vitals"].items():
            if v["level"] == "watch" or v["score"] == 0:
                continue
            actions.append({
                "country": country,
                "vital": vital,
                "level": "urgent" if v["level"] == "alarm" else "preventive",
                "dispatch": "human_required" if v["level"] == "alarm" else "advisory",
                "score": v["score"],
                "action": PLAYBOOK[vital],
                "evidence_events": v["evidence_events"],
            })
    return sorted(actions, key=lambda a: -a["score"])
