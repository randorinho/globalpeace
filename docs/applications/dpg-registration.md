# Digital Public Good Registration — Application Draft

Submit at: https://www.digitalpublicgoods.net/submission-guide
Prepared 2026-10-12. Paste-ready answers per DPG Standard indicator; every
claim links to public evidence in this repository or the live platform.

---

**Name**: globalpeace.ai
**Type**: Open-source software (platform) producing open content (verified
conflict-event records, verification trails, published analyses)
**Website**: https://globalpeace.ai
**Repository**: https://github.com/randorinho/globalpeace
**Contact**: Ricardo Andorinho — randorinho@mbuintelligence.com
**Description (short)**: An open peace-intelligence platform: it ingests
conflict-related reporting from institutional and vetted sources, audits
every claim with transparent rules plus multi-agent AI analysis, publishes
verified events with full verification trails on a world map, monitors each
country's vital systems through an independent Human Rights Agent, and
drafts concrete, evidence-cited political and economic approaches for
peace — with human accountability for any outbound action.

## 1. Relevance to the SDGs

Primary: **SDG 16 — Peace, Justice and Strong Institutions.**
- 16.1 (reduce violence): early detection and verification of conflict
  events; country vital-signs monitoring with graded alerts; machine-drafted
  preventive options (dialogue, mediation, humanitarian access) for
  decision-makers. Evidence: https://globalpeace.ai (map, verification
  trails, "Suggested approaches for peace"); docs/ARCHITECTURE.md.
- 16.6 (accountable, transparent institutions): append-only decision
  trails; public verification journeys per event; the platform's own AI
  rights-auditor publishes critiques of the platform itself. Evidence:
  docs/HUMAN_RIGHTS_AGENT.md; /api/public/hra/positions.
- 16.10 (public access to information): all verified intelligence is
  public, free, and attributed; same methodology for every country.
Secondary: SDG 2 (famine early-warning signals), SDG 17 (data partnership
with institutional sources: ReliefWeb, IOM, UNHCR, FEWS NET ecosystems).

## 2. Open licensing

**AGPL-3.0** (OSI-approved), repository-wide:
https://github.com/randorinho/globalpeace/blob/dev/LICENSE
Published event records and analyses are served through open JSON APIs
(/api/public/*) for free reuse with attribution.

## 3. Clear ownership

Code and documentation are owned by the project maintainer (Ricardo
Andorinho), published under AGPL-3.0 in the public repository; the funding
model (docs/FUNDING.md) commits to transfer into a Portuguese non-profit
association as institutional ownership. Source data remains attributed to
originating publishers (ReliefWeb, IOM, SIPRI, etc.) per their terms;
every public record carries its source attribution.

## 4. Platform independence

Fully self-hostable from the repository: PostgreSQL/PostGIS, Neo4j,
OpenSearch, Redpanda, FastAPI, React/MapLibre — all open source, composed
via docker-compose (infra/). Optional external components and their open
alternatives:
- Cloudflare edge (Workers/Tunnel): deployment convenience only; the origin
  stack runs standalone behind any reverse proxy (nginx/Caddy).
- Anthropic Claude for the analyst/solutions agents: the pipeline degrades
  gracefully to the transparent rules engine without it (documented in
  docs/AUDIT_CRITERIA.md), and the agent layer is provider-portable (JSON
  schema contracts).
- Map base tiles (MapLibre demo tiles): any self-hosted OpenMapTiles source.

## 5. Documentation

Public, in-repo: README (architecture + quickstart), docs/ARCHITECTURE.md,
DATA_MODEL.md, AUDIT_CRITERIA.md, GOVERNANCE.md, COMPLIANCE.md,
HUMAN_RIGHTS_AGENT.md, per-component READMEs (backend, pipelines, edge),
reproducible local setup via docker-compose, CI as executable documentation.

## 6. Mechanism for extracting data and content

All published content is available as JSON over open endpoints without
authentication: /api/public/events, /api/public/events/{id}/trail,
/api/public/hra/positions, /api/public/solutions, /api/public/arms-transfers.
Database-level export via standard pg_dump (documented backup tooling,
scripts/backup.sh). No PII is collected from the public (see 9a).

## 7. Adherence to privacy and applicable laws

docs/COMPLIANCE.md maps controls to EU AI Act expectations: record-keeping
(append-only logs, git-versioned registries), human oversight (machine
outputs labeled; urgent actions require human dispatch), transparency
labels, data minimisation. GDPR posture: the platform collects no user
accounts and no personal data from visitors; public contributions are
screened to REJECT submissions containing emails/phone numbers; rate-limit
keys are hashed in memory and never stored. Jurisdiction: Portugal/EU.

## 8. Adherence to standards & best practices

Open standards: HTTP/JSON APIs, GeoJSON, ISO 3166 country codes, OpenAPI
(FastAPI-generated), SQL migrations (Alembic), OSI licensing. Engineering
practice: CI on all PRs (tests + typecheck + builds), protected main branch,
append-only audit structures, documented design system (docs/DESIGN.md,
docs/BRANDBOOK.md) with WCAG-checked contrast and color-vision-safe scales.

## 9. Do no harm by design

The platform's constitution is harm-prevention-first (docs/GOVERNANCE.md):
"If information could endanger a person, the platform must not publish it
automatically — even when the information is accurate."

**9a. Data privacy & security**: no public user accounts; PII screen
rejects personal data in contributions; machine publication is
exposure-gated (events naming individuals or exact coordinates are never
auto-published — human review required); public verification trails expose
actor classes, never identities; secrets management and security
boundaries verified on every deploy (scripts/deploy.sh fails the deploy on
a security regression).

**9b. Inappropriate & illegal content**: ingestion is source-gated
(institutional + human-ratified vetted sources only; agentic vetting panel
screens new sources for fabrication/manipulation, docs/AUDIT_CRITERIA.md);
public contributions are quarantined as unverified claims, never published
automatically; moderation is human with an auditable trail.

**9c. Protection from harassment**: no user-to-user interaction surface
exists (no comments, no profiles); contributions are write-only into a
moderation queue; the data model prohibits villain-rankings and the
actor-graph publication rules prohibit naming individuals
(docs/DATA_MODEL.md), protecting both subjects and contributors.

---

### Submission notes (not part of the form)

- Submit after: fiscal host confirmation (Open Collective Europe) so the
  "organisation" field has an entity behind it — or submit as individual
  maintainer now; DPGA accepts community projects.
- Reviewers may probe indicator 4 (Claude dependency): the honest line is
  the one above — core verification runs without any proprietary service;
  the agent layer is optional and portable.
