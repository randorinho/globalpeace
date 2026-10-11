# Human Rights Agent (HRA)

An independent agent inside the platform's infrastructure with three organs
(pipelines/hra):

## 1. The immune system (vitals.py — independent algorithm)

A deterministic, fully auditable algorithm — not an LLM — that treats each
country's **vital systems** the way an immune system treats an organism:
continuous monitoring, graded response, memory.

- **Vitals**: civilian safety, population stability, food security, health
  system, humanitarian access.
- **Signal**: every tracked event contributes, weighted by the verification
  ladder (verified 1.0 → ai_corroborated 0.6 → unverified 0.25), decayed on a
  14-day half-life (real time), amplified by reported civilian impact.
- **Response levels**: watch → concern → alarm. Breaches trigger the
  **immune response**: an immediately prioritized list of diplomatic actions
  from the preventive playbook, each citing its evidence events.
- **Constitutional line**: urgent (alarm-level) actions are *flagged for
  human dispatch* — the agent prioritizes immediately; it never contacts any
  external party itself (GOVERNANCE.md; APDSI Art. 86-C).
- **No rankings**: vitals are per-country absolute conditions, never a league
  table.

## 2. The development auditor (dev_audit.py — Claude agent)

Audits **the platform itself**: criteria files, security policy, governance
docs, recent commits — for exposure risks to individuals, country-treatment
bias, human-accountability drift, and manipulation surface. Advisory and
published; it cannot change platform behavior.

## 3. The published position (run.py + /public/hra/*)

Every pipeline cycle (30 min) the agent recomputes vitals from live events,
re-audits development, drafts a grounded position statement (LLM-drafted from
computed data only, deterministic fallback), and **publishes** it:

- `GET /public/hra/position` — current position (also rendered on the map page)
- `GET /public/hra/positions` — append-only history: the agent's position
  over time is itself a public record

## Independence guarantees

- Own criteria file; reads events, cannot write verification statuses.
- Publishes without operator pre-approval, within publication rules:
  no personal data, no exact-location inference, no rankings.
- Its platform critiques are published verbatim alongside its position —
  including criticisms of the operator's own decisions.
