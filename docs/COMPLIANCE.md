# Compliance Notes — AI-Act-Oriented Controls

Working mapping of platform controls to EU AI Act expectations (logging,
human oversight, transparency, data governance). An engineering document,
not legal advice; counsel review is a backlog item.

## Logging & external auditability (Art. 12-style record-keeping)

| Record | Where | Properties |
|---|---|---|
| Source vetting panels & human ratifications | `pipelines/vetting/audit_log.jsonl` + `registry.yaml` | Append-only JSONL; git-versioned in the **public repository** — tamper-evident, externally inspectable without our cooperation |
| Verification decisions (human and machine) | `review_decisions` table | Append-only by construction (no update/delete endpoints); machine promotions attributed to `ai-pipeline(continental-desks)` |
| AI audits per event | `events.ai_audit` + decision trail | Engine version, per-lens concerns, consensus counts, timestamps |
| HRA positions | `hra_positions` table, public endpoints | Append-only public history of the agent's assessments **and its critiques of the platform** |
| Pipeline executions | `~/Library/Logs/gpai/` | Every scheduled ingest/audit/position cycle |
| Ingested items | events carry source URL, language, feed confidence prior | Dedupe ledger records every fetch decision |

## Closed-context agents (no autonomous data gathering)

All LLM agents (continental audit desks, vetting panel, HRA auditor,
statement drafter) operate **only on data passed to them by deterministic,
logged platform code**: event digests, fetched source samples, our own
documents. No agent has browsing, search, or tool access; no agent ingests
anything the pipeline did not log first. Public contributions are quarantined
claims and are never fed to agents without moderation.

## Human oversight (Art. 14-style)

- Machines never verify: `ai_corroborated` is a labeled machine tier, bounded
  (fail-closed, exposure-gated), never overriding human decisions, with a
  hard expiry (2027-01-11) in REVIEW_SECURITY_POLICY.md.
- Urgent diplomatic priorities are flagged `human_required` — no automatic
  external action of any kind.
- Source trust: machine vetting is provisional; promotion to a corroborating
  channel requires logged human ratification (`vetting/ratify.py`).

## Transparency (Art. 13/50-style)

- Every public event carries its verification status label; machine
  corroboration is visually and verbally distinct from human review.
- Public verification trails expose each event's journey (sanitized).
- The platform's own self-audit (HRA) is published, including open concerns.

## Data minimisation

- PII screen on public contributions; pseudonymisation commitments in
  GOVERNANCE.md; public trails expose actor *classes* (operator / ai-pipeline),
  never personal identifiers; rate-limit keys hashed in memory, not stored.
