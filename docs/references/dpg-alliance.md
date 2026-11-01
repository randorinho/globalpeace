# Digital Public Goods Alliance — the standard this platform registers under

> **Reference document** (information_type: `interpretation` — summary with
> links to the originals; not platform policy). Added 2026-11-01. The
> platform's paste-ready application lives at
> [../applications/dpg-registration.md](../applications/dpg-registration.md).

## What the Alliance is

The Digital Public Goods Alliance (DPGA) is a multi-stakeholder initiative —
endorsed by the UN Secretary-General's Roadmap for Digital Cooperation and
referenced in the Global Digital Compact — that maintains the **DPG
Standard** and the public **DPG Registry** of solutions recognized as digital
public goods: open-source software, open data, open AI systems and open
content that help attain the Sustainable Development Goals.

- Standard: https://www.digitalpublicgoods.net/standard (CC-BY-SA 4.0,
  maintained by the DPGA Secretariat)
- Registry & submission: https://www.digitalpublicgoods.net/submission-guide

## The DPG Standard — nine indicators

| # | Indicator | What it requires | Where globalpeace.ai answers it |
|---|---|---|---|
| 1 | SDG relevance | Demonstrable advancement of the SDGs | SDG 16 (peace, justice, institutions); SDG 2, 17 — application §1 |
| 2 | Open licensing | OSI-approved / Open Definition license | AGPL-3.0, repository-wide |
| 3 | Clear ownership | Documented ownership | Maintainer-owned, public repo — application §3 |
| 4 | Platform independence | No mandatory proprietary dependency | Open stack (FastAPI, PostgreSQL, OpenSearch, Neo4j, React); open JSON APIs |
| 5 | Documentation | Enough for an independent deployment | docs/ARCHITECTURE.md, DATA_MODEL.md, infra/ compose + scripts |
| 6 | Mechanism for extracting data | Non-proprietary export of data | /api/public/* JSON; append-only trails |
| 7 | Privacy & applicable laws | Compliance with relevant laws | docs/COMPLIANCE.md; PII screens on contributions |
| 8 | Standards & best practices | Open standards adherence | ISO 3166, GeoJSON, OpenAPI; DCO sign-off (CONTRIBUTING.md) |
| 9 | Do no harm by design | 9A data privacy & security; 9B inappropriate/illegal content; 9C protection from harassment | Edge-gated origin, data minimisation (hashed client keys), moderation-only contributions, pseudonymisation rule, exposure gate (no actor names/exact locations promoted by machine) |

## Why registration matters for peace

DPG recognition is the institutional bridge between this platform and the UN
digital-cooperation agenda: registered DPGs are discoverable by governments
and UN agencies implementing the Global Digital Compact, and recognition is
evidence of the governance properties (openness, do-no-harm, auditability)
that make peace intelligence trustworthy enough to act on. Status: draft
application complete (all 9 indicators, evidence-linked); submission pending.
