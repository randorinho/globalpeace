"""Transparent-rules audit engine (docs/AUDIT_CRITERIA.md).

Distinguishes publication authenticity, substantive credibility, and
independent corroboration. A figure is NOT verified because a credible source
cites it — the cross-check matrix below names the primary dataset a human
reviewer must consult. Any doubt -> needs_additional_verification.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

FRESH_DAYS = 3
RECENT_DAYS = 14

# Publication-authenticity tiers by source domain (suffix match).
INSTITUTIONAL = (
    "reliefweb.int", "un.org", "unhcr.org", "wfp.org", "who.int", "unocha.org",
    "fews.net", "acleddata.com", "icrc.org", "data.humdata.org",
)
KNOWN_NGO = ("msf.org", "savethechildren.net", "nrc.no", "rescue.org", "crisisgroup.org")

# Cross-check matrix: claim-type patterns -> primary dataset a human must check.
CROSS_CHECKS: list[tuple[str, str, str]] = [
    # English + French stems — the pilot ingests both (docs/ROADMAP.md: 5-10 languages)
    (r"refugee|r[ée]fugi|displac|d[ée]plac|arriv|idp\b|flee|fled|returns?\b|retour|urgence",
     "refugee_figures", "cross-check with UNHCR (and national government) data"),
    (r"attack|attaque|clash|violen|killed|tu[ée]s|incident|conflict event|affected [\d,]+ people",
     "conflict_figures", "cross-check against ACLED's underlying dataset; interpret 'affected N people' per ACLED methodology"),
    (r"price|prix|march[ée]|market|food insecur|ins[ée]curit[ée] alimentaire|famine|harvest|r[ée]colte|lean season|soudure",
     "market_figures", "compare with FEWS NET market data and local market-monitoring sources"),
    (r"cholera|measles|epidemic|health needs|malnutrition",
     "health_figures", "cross-check with WHO/UNICEF surveillance data"),
]


def source_tier(urls: list[str]) -> tuple[str, float]:
    if not urls:
        return "none", 0.1
    best = ("unknown", 0.4)
    for u in urls:
        host = urlparse(u).hostname or ""
        if any(host == d or host.endswith("." + d) for d in INSTITUTIONAL):
            return "institutional", 0.8
        if any(host == d or host.endswith("." + d) for d in KNOWN_NGO):
            best = ("known_ngo", 0.6)
    return best


def recency(date_time: str, now: datetime) -> tuple[str, float, float]:
    dt = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    days = (now - dt).total_seconds() / 86400
    if days < FRESH_DAYS:
        return "fresh", 1.0, days
    if days <= RECENT_DAYS:
        return "recent", 0.7, days
    return "stale", 0.2, days


def required_cross_checks(text: str) -> dict[str, str]:
    checks: dict[str, str] = {}
    for pattern, key, instruction in CROSS_CHECKS:
        if re.search(pattern, text, re.I):
            checks[key] = instruction
    return checks


def corroboration(event: dict, all_events: list[dict]) -> int:
    """Other events, same country, within ±7 days, from a different source domain."""
    def domains(ev):
        return {urlparse(u).hostname for u in ev.get("source_urls", [])}

    dt = datetime.fromisoformat(event["date_time"].replace("Z", "+00:00"))
    mine = domains(event)
    n = 0
    for other in all_events:
        if other["event_id"] == event["event_id"] or other["country"] != event["country"]:
            continue
        odt = datetime.fromisoformat(other["date_time"].replace("Z", "+00:00"))
        if abs((odt - dt).total_seconds()) > 7 * 86400:
            continue
        if domains(other) - mine:
            n += 1
    return n


def audit_event(event: dict, all_events: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    text = f"{event.get('title','')} {' '.join(event.get('source_urls', []))}"

    tier, tier_score = source_tier(event.get("source_urls", []))
    rec_label, rec_score, age_days = recency(event["date_time"], now)
    checks = required_cross_checks(text)
    corrob = corroboration(event, all_events)
    specificity = sum([bool(event.get("title")), bool(event.get("source_urls")),
                       event.get("location") is not None, bool(event.get("actors"))]) / 4

    reasons: list[str] = []
    if tier == "institutional":
        reasons.append(f"publication authenticity high ({tier})")
    else:
        reasons.append(f"source tier '{tier}' — publication authenticity needs confirmation")
    reasons.append(f"{rec_label}: {age_days:.1f} days old")
    if corrob:
        reasons.append(f"corroborated by {corrob} other-source event(s), same country ±7d")
    else:
        reasons.append("no independent corroboration among ingested events")
    for key, instruction in checks.items():
        reasons.append(f"{key}: cited figures are not independently verified — {instruction}")

    score = round(0.4 * tier_score + 0.25 * rec_score
                  + 0.2 * min(corrob, 3) / 3 + 0.15 * specificity, 3)

    # Any doubt -> needs_additional_verification. credible_recent requires an
    # institutional source, recency, corroboration, and NO pending cross-checks.
    if rec_label == "stale":
        verdict = "stale_low_priority"
    elif tier == "institutional" and corrob > 0 and not checks and rec_label in ("fresh", "recent"):
        verdict = "credible_recent"
    else:
        verdict = "needs_additional_verification"

    return {
        "verdict": verdict,
        "score": score,
        "signals": {
            "source_tier": tier, "recency": rec_label, "age_days": round(age_days, 1),
            "corroborating_events": corrob, "specificity": specificity,
        },
        "reasons": reasons,
        "cross_checks": checks,
        "engine": "rules-v1",
    }
