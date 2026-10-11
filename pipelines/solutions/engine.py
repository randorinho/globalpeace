"""The solutions agents: concrete approaches for peace, political and
economic, drafted per situation by two lensed agents.

Hard rules (encoded in the system prompts, enforced by schema):
- Grounded ONLY in the situation digest provided (tracked events + vitals).
- Institutional enabling actors only — never named individuals.
- Every approach carries rationale, evidence event ids, risks, and
  what_would_make_this_wrong — options for diplomats, never commands.
- information_type: recommendation (docs/DATA_MODEL.md) — machine-drafted,
  advisory; nothing here is dispatched automatically.
"""
from __future__ import annotations

import json
import sys

APPROACH_SCHEMA = {
    "type": "object",
    "properties": {
        "approaches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "approach": {"type": "string",
                                 "description": "the concrete course of action, 2-4 sentences, operational not aspirational"},
                    "rationale": {"type": "string",
                                  "description": "why now, grounded in the cited events/vitals"},
                    "enabling_actors": {"type": "array", "items": {"type": "string"},
                                        "description": "institutions only (e.g. AU, IGAD, UNHCR, World Bank, regional chambers of commerce)"},
                    "evidence_event_ids": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "string"},
                    "what_would_make_this_wrong": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["exploratory", "moderate", "strong"]},
                },
                "required": ["title", "approach", "rationale", "enabling_actors",
                             "evidence_event_ids", "risks", "what_would_make_this_wrong", "confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["approaches"],
    "additionalProperties": False,
}

LENSES = {
    "political": """You are the POLITICAL solutions agent of a peace-intelligence platform. \
For the situation digest provided, draft 2-3 concrete political approaches that could \
reduce harm or open paths to de-escalation: dialogue formats, mediation tracks, regional-\
organisation engagement, ceasefire-adjacent mechanisms, humanitarian diplomacy, \
confidence-building measures. Operational, not aspirational: who convenes what, toward \
which first step.""",
    "economic": """You are the ECONOMIC solutions agent of a peace-intelligence platform. \
For the situation digest provided, draft 2-3 concrete economic approaches that could \
reduce harm or underpin stability: humanitarian financing instruments, market and price \
stabilisation, cross-border trade and remittance channels, local procurement, livelihood \
protection, reconstruction sequencing. Operational, not aspirational: which instrument, \
funded or enabled by whom, toward which first effect.""",
}

COMMON_RULES = """
Hard rules:
- Use ONLY the digest: cite evidence_event_ids from it; if evidence is thin, say so via confidence=exploratory.
- Enabling actors are INSTITUTIONS only — never a named individual.
- These are options for human decision-makers, never commands; include real risks and what would make the approach wrong.
- Never reward aggression, never propose anything that endangers civilians or identifiable communities, no country rankings."""


def draft_approaches(situation: dict) -> dict | None:
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic()
    out: dict[str, list] = {}
    for lens, prompt in LENSES.items():
        try:
            response = client.messages.create(
                model="claude-opus-5",
                max_tokens=16000,
                system=prompt + COMMON_RULES,
                output_config={"format": {"type": "json_schema", "schema": APPROACH_SCHEMA}},
                messages=[{"role": "user", "content":
                           "Situation digest:\n" + json.dumps(situation, indent=1)[:30000]}],
            )
            if response.stop_reason in ("refusal", "max_tokens"):
                print(f"  solutions/{lens}: {response.stop_reason}", file=sys.stderr)
                continue
            data = json.loads(next(b.text for b in response.content if b.type == "text"))
            for a in data["approaches"]:
                a["level"] = lens
            out[lens] = data["approaches"]
        except Exception as exc:  # noqa: BLE001
            print(f"  solutions/{lens}: {type(exc).__name__}", file=sys.stderr)
    if not out:
        return None
    return {"approaches": [a for lst in out.values() for a in lst],
            "model": "claude-opus-5"}
