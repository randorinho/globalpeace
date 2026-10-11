"""The Human Rights Agent's second mandate: audit OUR development.

An independent Claude agent reviews the platform's own criteria, policies,
and recent development activity against human-rights principles (exposure
risk, bias between countries, governance drift, manipulation surface).
Advisory and published — it cannot change platform behavior itself.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent.parent

SCHEMA = {
    "type": "object",
    "properties": {
        "compliance_concerns": {"type": "array", "items": {"type": "string"}},
        "exposure_risks": {"type": "array", "items": {"type": "string"},
                           "description": "ways current behavior could endanger individuals or communities"},
        "bias_observations": {"type": "array", "items": {"type": "string"},
                              "description": "unequal treatment between countries/regions in criteria or coverage"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "overall": {"type": "string", "enum": ["aligned", "aligned_with_concerns", "misaligned"]},
    },
    "required": ["compliance_concerns", "exposure_risks", "bias_observations",
                 "recommendations", "overall"],
    "additionalProperties": False,
}

SYSTEM = """You are the independent Human Rights Agent of a peace-intelligence \
platform, auditing the PLATFORM ITSELF — its criteria, policies, and recent \
development — not the conflicts it tracks. Your charter:
- People first: flag anything that could expose individuals or communities \
(precise locations, identifiable testimonies, data that aids targeting).
- Equal treatment: the same methodology must apply to every country; flag \
coverage or criteria asymmetries that privilege or villainize any state or group.
- Human accountability: machines may recommend, label, and prioritize; flag any \
drift toward machine-decided verification or automatic external action.
- Anti-manipulation: flag weaknesses that political actors could exploit \
(open write paths, trust-promotion gaming, review capture).
Be specific and cite the document or behavior you are flagging. If something is \
genuinely sound, do not manufacture findings."""


def gather_inputs() -> dict:
    def read(p: str, limit: int = 6000) -> str:
        f = REPO / p
        return f.read_text()[:limit] if f.exists() else "(missing)"

    log = subprocess.run(
        ["git", "-C", str(REPO), "log", "--oneline", "-25"],
        capture_output=True, text=True,
    ).stdout
    return {
        "audit_criteria": read("docs/AUDIT_CRITERIA.md"),
        "review_security_policy": read("docs/REVIEW_SECURITY_POLICY.md"),
        "governance_excerpt": read("docs/GOVERNANCE.md", 3000),
        "recent_development": log,
    }


def audit_development() -> dict | None:
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,
            system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content":
                       "Platform state to audit:\n" + json.dumps(gather_inputs(), indent=1)[:40000]}],
        )
        if response.stop_reason == "refusal":
            return {"error": "agent declined"}
        if response.stop_reason == "max_tokens":
            return {"error": "truncated"}
        return {**json.loads(next(b.text for b in response.content if b.type == "text")),
                "model": "claude-opus-5"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"unavailable: {type(exc).__name__}"}


STATEMENT_SYSTEM = """You write the public position statement of the Human Rights \
Agent of a peace-intelligence platform. You are given ONLY computed data: per-country \
vital-system assessments, the prioritized action list, and the platform self-audit. \
Rules: ground every sentence in that data — no new facts, no speculation about intent, \
no country rankings, no names of individuals. State conditions, priorities, and what \
must be independently verified. 120-200 words, sober institutional voice."""


def draft_statement(assessment: dict, actions: list[dict], dev_audit: dict | None) -> str | None:
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=4096,
            system=STATEMENT_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(
                {"vitals": assessment, "priorities": actions[:8], "self_audit": dev_audit}, indent=1)[:30000]}],
        )
        if response.stop_reason == "refusal":
            return None
        return next(b.text for b in response.content if b.type == "text").strip()
    except Exception:  # noqa: BLE001
        return None
