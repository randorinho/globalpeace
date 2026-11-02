GIve me the exact wteps # Cloud & AI Credit Programs — Application Drafts

Prepared 2026-11-02. Common core + per-program notes. These cover
infrastructure and inference costs pre-grant (docs/FUNDING.md, Phase 0).

## Common core (reuse across forms)

**Organization / project**: globalpeace.ai — open peace-intelligence
platform. AGPL-3.0, public repository
(https://github.com/randorinho/globalpeace), live at https://globalpeace.ai.
Digital Public Good registration in progress; funding policy public at
https://globalpeace.ai/#/funding.

**Mission (50 words)**: Detect risks of violence early, verify claims
transparently, and put evidence-cited, human-accountable options for peace in
front of decision-makers — for every country, with the same published
methodology. Final decisions remain human, institutional, and legally
accountable.

**What the credits power**:
- Ingestion pipelines over institutional sources (UN News, ReliefWeb, IOM,
  SIPRI; ACLED/UNHCR/UCDP integrations pending access approvals).
- Six continental AI analyst desks (adversarial audit panels) + political and
  economic solutions agents — the main inference cost.
- Data layer: PostgreSQL/PostGIS, OpenSearch, Neo4j; public JSON APIs and a
  React/MapLibre world map.

**Current monthly cost (baseline)**: ~€20 VPS (Hetzner, EU) + AI inference
(Anthropic API; scales with event volume as coverage grows from 6 to all
countries). Credits extend coverage and audit depth, not overhead.

**Safeguards relevant to responsible-AI review**: machine outputs are
advisory and labeled; no automatic dispatch; append-only audit trails;
exposure gates (no individual names or exact locations auto-published);
do-no-harm design per DPG Standard indicator 9; EU AI-Act-oriented controls
(docs/COMPLIANCE.md).

## Per-program notes

### Microsoft — AI for Good / AI for Humanitarian Action
https://www.microsoft.com/en-us/ai/ai-for-good
- Angle: early warning + humanitarian response; Azure credits would host a
  mirrored origin and OpenSearch at scale.
- They favor measurable outcomes: cite events verified/month, countries
  covered, time-from-report-to-verified metrics (available from our logs).

### Google.org / Google for Nonprofits + Google Cloud credits
https://www.google.org · https://cloud.google.com/nonprofits
- Nonprofit programs generally require registered-nonprofit status → viable
  after the Open Collective Europe fiscal host is in place (OCE umbrella) or
  the Portuguese associação exists. Note this dependency in sequencing.
- Angle: information integrity (Global Digital Compact alignment).

### AWS — Open Data / Imagine Grant / Activate-style credits
https://aws.amazon.com/government-education/nonprofits/
- Imagine Grant is US-501(c)(3)-centric; the open-source credits route and
  AWS Open Data sponsorship (hosting our verified-events dataset publicly)
  fit better for an EU project.
- Angle: the verified-events corpus as an open dataset (CC-BY-style
  attribution terms for content; AGPL for code).

### Anthropic — (inference is our largest AI cost)
- Watch for research/social-impact API credit programs; our audit-desks
  architecture (six continental panels, doubt-only, human-gated) is a strong
  responsible-deployment story.

## Sequencing

1. Open Collective Europe first (unlocks nonprofit-gated programs).
2. Microsoft + AWS applications in parallel (least entity-dependent).
3. Google.org after fiscal host confirmation.
