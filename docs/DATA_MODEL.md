# Data Model

## Information taxonomy

The system must clearly distinguish **five types of information**:

1. **Observed fact** — something confirmed by a source.
2. **Claim** — information that has not yet been verified.
3. **Interpretation** — analysis produced by researchers or AI.
4. **Forecast** — a probability or future scenario.
5. **Recommendation** — a possible response, never an automatic command.

> Never present a forecast as a fact. The interface must show the source, publication date, confidence level, verification status, and disagreements between sources.

## Event schema

```json
{
  "event_id": "unique-id",
  "date_time": "UTC",
  "location": "geographic coordinates",
  "country": "country code",
  "actors": [],
  "event_type": "protest|attack|negotiation|displacement",
  "source_urls": [],
  "source_language": "en",
  "confidence": 0.78,
  "verification_status": "partially_verified",
  "civilian_impact": {},
  "human_review": false,
  "last_updated": "UTC timestamp"
}
```

## Social and war graph

The graph represents more than military confrontations. Node types:

- States and governments
- Armed groups
- Political parties and social movements
- Communities, cities, and regions
- Humanitarian organisations
- Mediators and diplomats
- Companies and economic networks
- Arms and resource routes (where reliable data exists)
- Events with time and geographic dimensions

Relationship types include cooperation, dependence, rivalry, mediation, and influence.

### Relationship attributes

Each relationship carries:

- Relationship type
- Start and end date
- Source
- Confidence level
- Degree of contestation
- Potential impact
- Risk of exposing vulnerable people

### Design constraint

Avoid creating a ranking of "bad countries." The graph displays **relationships, evidence, and uncertainty** — it must never turn entire populations into villains.

### Actor-graph publication rules (decision on HRA finding #3)

Publicly served graph data is limited to **documented state-to-state
relationships from citable datasets** (e.g. SIPRI arms transfers), always with
attribution. The public graph must not include: named individuals; sub-national
or non-state armed-actor links; or inferred (non-documented) relationships.
Expanding any of these requires council-level review (docs/GOVERNANCE.md
institutional model) — targeting and defamation risk is real even when the
underlying data is accurate.
