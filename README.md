# globalpeace.ai — Global Peace Intelligence Platform

A global, open, and responsible **peace-intelligence infrastructure** that transforms verified information into understanding, dialogue, and preventive action — while protecting communities and keeping critical decisions under human responsibility.

## What this is (and is not)

This is a **peace-intelligence platform**, not an autonomous agent that makes diplomatic decisions. The system collects signals, verifies information, explains risks, presents scenarios, and recommends options to diplomats and authorised organisations. **Final decisions remain human, institutional, and legally accountable.**

The platform does not promise to "end all wars" or act on behalf of the United Nations. It supports existing UN structures for prevention, mediation, peacebuilding, and peacekeeping — it does not replace them.

## Purpose

To detect risks of violence at an early stage, improve understanding between communities, amplify local solutions, and support evidence-based diplomatic decisions.

The approach is **locally led, inclusive, and focused on prevention, trust, justice, and institutional strengthening**. Local peace actors are often the first to identify rising tensions and understand community-level causes and solutions.

## Architecture at a glance

```
Global sources
    ↓
Ingestion and connectors
    ↓
Normalisation + translation
    ↓
Verification and credibility assessment
    ↓
Event, actor, and relationship graph
    ↓
Risk and escalation-detection models
    ↓
AI analyst with cited sources
    ↓
Human review and governance
    ↓
Dashboard, alerts, reports, and diplomatic channels
```

See the full documentation:

| Document | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Source layer, connectors, tech stack, risk engine, AI agents |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Information taxonomy, event schema, social/war graph |
| [docs/GOVERNANCE.md](docs/GOVERNANCE.md) | Security, ethics, privacy, public participation, institutional model |
| [docs/PRIORITIZATION.md](docs/PRIORITIZATION.md) | How every ordering (agent emphasis, event sort, proposal rank) traces to published frameworks |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 90-day MVP pilot and first functional version |
| [docs/CLOUDFLARE.md](docs/CLOUDFLARE.md) | Edge/origin split — domain and edge layer on Cloudflare |
| [docs/references/apdsi-un-charter-reform.md](docs/references/apdsi-un-charter-reform.md) | APDSI letter: UN Charter reform proposal on autonomous-systems governance (reference) |
| [docs/references/un-peace-and-digital-framework.md](docs/references/un-peace-and-digital-framework.md) | UN anchors: Pact for the Future (A/RES/79/1), New Agenda for Peace, Global Digital Compact |
| [docs/references/dpg-alliance.md](docs/references/dpg-alliance.md) | Digital Public Goods Alliance and the 9-indicator DPG Standard this platform registers under |
| [docs/references/internet-society.md](docs/references/internet-society.md) | Internet Society: the open Internet as peace infrastructure; shutdown data as a future signal |
| [docs/references/clube-lisboa-mne-brief.md](docs/references/clube-lisboa-mne-brief.md) | Clube de Lisboa × MNE round-table brief: Charter erosion, unregulated new warfare, Portugal's UNSC posture |
| [docs/BACKLOG.md](docs/BACKLOG.md) | Internal backlog — P0 operational trust → P2 Solutions Engine → DevEx |
| [docs/REVIEW_SECURITY_POLICY.md](docs/REVIEW_SECURITY_POLICY.md) | DRAFT — controls required before human-review expansion; interim AI-corroboration regime |
| [docs/HUMAN_RIGHTS_AGENT.md](docs/HUMAN_RIGHTS_AGENT.md) | Independent HRA: vitals immune system, development auditor, published position |
| [docs/COMPLIANCE.md](docs/COMPLIANCE.md) | AI-Act-oriented controls: logging, closed-context agents, human oversight, transparency |
| [docs/BRANDBOOK.md](docs/BRANDBOOK.md) | Identity: the pulse mark, core palette, conflict-pressure scale, sharing assets |
| [docs/FUNDING.md](docs/FUNDING.md) | Public & non-profit funding model: principles, fiscal host, DPG path, grant pipeline |

## Repository layout

```
backend/    FastAPI origin API — event model, risk engine
edge/       Cloudflare Workers — API gateway (wrangler)
pipelines/  Ingestion connectors, normalisation, verification (Kafka/ETL)
frontend/   React + MapLibre dashboard and public site
infra/      docker-compose, deployment, observability
docs/       Architecture and governance documentation
```

## License

[GNU AGPL-3.0](LICENSE) — the platform and any network-hosted derivative stay
open. A peace commons cannot be captured into a closed service.

## Core safety rule

> If information could endanger a person, the platform must not publish it automatically — even when the information is accurate.

## Ownership and license

Copyright © 2026 Ricardo Andorinho.

globalpeace.ai — its code, documentation, and original published content —
is owned by its maintainer, **Ricardo Andorinho**, and released as free
software under the [GNU AGPL-3.0](LICENSE). Contributions enter under the
same license with a DCO sign-off ([CONTRIBUTING.md](CONTRIBUTING.md)).
Source data remains the property of its originating publishers (ReliefWeb,
IOM, SIPRI, UN News, etc.) and is republished with attribution per their
terms; every public record carries its source attribution. The project's
[funding model](docs/FUNDING.md) commits to transferring institutional
ownership to a Portuguese non-profit association as the project scales —
with the public-good lock (open source, no proprietary fork) intact.
