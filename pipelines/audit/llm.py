"""Optional Claude analyst — an advisory second opinion on top of the rules.

It can ADD doubt (concerns the rules missed) and write a reviewer summary; it
can never upgrade the rules verdict or verify anything. Runs only when
Anthropic credentials are available; the pipeline works without it.
"""
from __future__ import annotations

import json

SCHEMA = {
    "type": "object",
    "properties": {
        "additional_concerns": {
            "type": "array", "items": {"type": "string"},
            "description": "Doubts the transparent rules missed; empty if none",
        },
        "agrees_with_rules_verdict": {"type": "boolean"},
        "reviewer_summary": {
            "type": "string",
            "description": "2-3 sentences for the human reviewer: what this claims, what must be checked before trusting it",
        },
    },
    "required": ["additional_concerns", "agrees_with_rules_verdict", "reviewer_summary"],
    "additionalProperties": False,
}

SYSTEM = """You are the audit analyst of a peace-intelligence platform. You assess \
incoming event claims BEFORE human review. Rules you operate under, strictly:
- You never verify. A figure is not verified because a credible publication cites it; \
only the primary dataset (UNHCR for refugee figures, ACLED for conflict-event counts, \
FEWS NET market data for prices) can verify it, and only a human records verification.
- Your job is doubt: name what must be independently checked and any credibility \
concern the transparent rules missed (methodology-sensitive figures, outdated coverage \
periods, single-sourced totals, headline/figure mismatches).
- Analytical sources (e.g. FEWS NET) publish analysis, not official government positions.
- Be concise and concrete; no speculation about actors' intent."""


def llm_opinion(event: dict, rules_audit: dict) -> dict | None:
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=2048,
            system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{
                "role": "user",
                "content": (
                    "Event claim:\n" + json.dumps({
                        "title": event.get("title"), "country": event.get("country"),
                        "event_type": event.get("event_type"), "date_time": event.get("date_time"),
                        "source_urls": event.get("source_urls"),
                    }, indent=2)
                    + "\n\nTransparent-rules audit:\n" + json.dumps(rules_audit, indent=2)
                    + "\n\nGive your advisory second opinion."
                ),
            }],
        )
        if response.stop_reason == "refusal":
            return {"error": "analyst declined", "model": "claude-opus-5"}
        text = next(b.text for b in response.content if b.type == "text")
        return {**json.loads(text), "model": "claude-opus-5"}
    except Exception as exc:  # noqa: BLE001 — audit must not fail on analyst errors
        return {"error": f"llm unavailable: {type(exc).__name__}"}
