"""Run a continental desk's analyst panel over its reporting digest.

Each of the six panelists is an independent Claude agent with a distinct
analytical lens, analysing the SAME digest (the desk's unaudited events with
their transparent-rules audits). Opinions are aggregated per event:
- every concern is kept, attributed to its lens;
- concerns raised independently by >=2 panelists -> panel_consensus;
- any concern downgrades credible_recent to needs_additional_verification.
Panels never verify and never upgrade a verdict (docs/AUDIT_CRITERIA.md).
"""
from __future__ import annotations

import json
import sys

from .continents import LENSES

PANEL_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "concerns": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["event_id", "concerns"],
                "additionalProperties": False,
            },
        },
        "digest_note": {
            "type": "string",
            "description": "1-2 sentences on digest-level patterns a reviewer should know",
        },
    },
    "required": ["events", "digest_note"],
    "additionalProperties": False,
}

SYSTEM_BASE = """You are one analyst on a six-agent continental audit desk of a \
peace-intelligence platform, reviewing the desk's current reporting digest BEFORE \
human review. Non-negotiable rules:
- You never verify. Only primary datasets (UNHCR, ACLED, FEWS NET market data, WHO) \
verify figures, and only a human records verification.
- Your output is doubt: concrete, checkable concerns. If an event raises none under \
your lens, return an empty concerns list for it — do not manufacture doubt.
- Never speculate about actors' intent; never rank countries.

Your analytical lens for this panel:
"""


def _digest_payload(events: list[dict]) -> str:
    return json.dumps([
        {
            "event_id": e["event_id"],
            "title": e.get("title"),
            "country": e.get("country"),
            "event_type": e.get("event_type"),
            "date_time": e.get("date_time"),
            "source_urls": e.get("source_urls"),
            "rules_audit": {k: e["_rules_audit"][k] for k in ("verdict", "reasons", "cross_checks")},
        }
        for e in events
    ], indent=1)


def run_panel(desk: str, events: list[dict], panel_size: int = 6) -> dict | None:
    """Returns {event_id: {"concerns": [...], "consensus": [...]}, "_digest_notes": [...]}
    or None when the LLM layer is unavailable."""
    try:
        import anthropic
    except ImportError:
        return None

    digest = _digest_payload(events)
    per_event: dict[str, list[tuple[str, str]]] = {e["event_id"]: [] for e in events}
    notes: list[str] = []
    ran = 0

    client = anthropic.Anthropic()
    for lens_name, lens_text in LENSES[:panel_size]:
        try:
            response = client.messages.create(
                model="claude-opus-5",
                max_tokens=4096,
                system=SYSTEM_BASE + lens_text,
                output_config={"format": {"type": "json_schema", "schema": PANEL_SCHEMA}},
                messages=[{
                    "role": "user",
                    "content": f"Desk: {desk}\n\nReporting digest:\n{digest}\n\n"
                               "Analyse every event under your lens.",
                }],
            )
            if response.stop_reason == "refusal":
                continue
            data = json.loads(next(b.text for b in response.content if b.type == "text"))
            ran += 1
            if data.get("digest_note"):
                notes.append(f"[{lens_name}] {data['digest_note']}")
            for item in data["events"]:
                if item["event_id"] in per_event:
                    for c in item["concerns"]:
                        per_event[item["event_id"]].append((lens_name, c))
        except Exception as exc:  # noqa: BLE001 — one panelist failing must not kill the desk
            print(f"  desk {desk}/{lens_name}: {type(exc).__name__}", file=sys.stderr)

    if ran == 0:
        return None

    result: dict = {"_digest_notes": notes, "_panelists_ran": ran}
    for event_id, tagged in per_event.items():
        # consensus: near-duplicate concerns from different lenses
        seen: dict[str, set[str]] = {}
        for lens_name, concern in tagged:
            key = " ".join(sorted(set(concern.lower().split()[:8])))
            seen.setdefault(key, set()).add(lens_name)
        consensus = [k for k, lenses in seen.items() if len(lenses) >= 2]
        result[event_id] = {
            "concerns": [f"[{ln}] {c}" for ln, c in tagged],
            "consensus_count": len(consensus),
        }
    return result
