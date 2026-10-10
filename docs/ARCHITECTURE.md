# Architecture

## Pipeline overview

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

## 1. Source layer

Sources are organised by confidence level:

- **Institutional sources** — United Nations agencies, humanitarian organisations, governments, international courts, regional organisations.
- **Conflict datasets** — ACLED, UCDP, ReliefWeb, HDX, and other specialist databases.
- **News sources** — international, regional, and local media, with particular attention to local languages and independent outlets.
- **Civil society** — humanitarian organisations, observatories, universities, local journalists, community networks.
- **Contextual data** — displacement, food prices, climate conditions, elections, sanctions, protests, access to healthcare, food security.
- **Public contributions** — ideas, testimonies, and alerts submitted by users, **always classified as claims until verified**.

ACLED provides data on political violence and protests, APIs, and the Conflict Alert System (forecasts of political violence by country/territory), plus downloadable datasets and programmatic API access.

## 2. Open-source connectors

Event-driven data pipelines with independent connectors:

- **RSS/Atom** — news and official statements.
- **REST/GraphQL APIs** — conflict, humanitarian, and statistical databases.
- **Ethical scrapers** — only where permitted by website terms.
- **CSV, JSON, GeoJSON, SDMX files** — official statistics.
- **Webhooks** — alerts from partner organisations.
- **Protected forms** — local contributions and reports.
- **Machine translation** — initial multilingual processing, followed by human validation for critical topics.

### Technology choices

| Concern | Options |
|---|---|
| Orchestration | Apache Airflow, Dagster, or Prefect |
| Messaging | Apache Kafka or Redpanda |
| ETL/ELT | Python, Apache NiFi, dbt |
| Raw storage | MinIO or S3-compatible storage |
| Analytical data | PostgreSQL, DuckDB, or ClickHouse |
| Geographic data | PostGIS |
| Graph database | Neo4j, Memgraph, or JanusGraph |
| Text search | OpenSearch |
| Vector search | pgvector, Qdrant, or Milvus |
| AI model serving | Hugging Face, vLLM, specialised models |
| Dashboard | React/Next.js, MapLibre, or deck.gl |
| Observability | OpenTelemetry, Prometheus, Grafana |

**Practical initial stack:** PostgreSQL + PostGIS + pgvector + Neo4j + Kafka + OpenSearch — rather than starting with too many technologies.

## 3. Risk-detection engine

Do **not** rely solely on a generative AI model. Combine:

- Transparent rules
- Time-series analysis
- Anomaly detection
- Classification models
- Graph-based models
- Geospatial analysis
- Multilingual language models
- Expert review

### Indicators

- Abnormal increase in violent incidents
- Inciting or dehumanising language
- Breakdown of negotiations
- Military mobilisation
- Rapid population displacement
- Humanitarian-access restrictions
- Sudden changes in food prices or availability
- Political arrests or violence against minorities
- Coordinated disinformation campaigns
- Breakdown of communication channels between actors

### Internal risk signal

```
R = w₁V + w₂D + w₃M + w₄H + w₅P − w₆C
```

where:

- **V** = observed violence
- **D** = inciting discourse
- **M** = mobilisation
- **H** = humanitarian impact
- **P** = political or economic pressure
- **C** = dialogue and containment capacity

This score is **not objective truth**. It functions as a triage signal, always accompanied by an explanation of the indicators that contributed to it.

## 4. Real-time recommendations

Recommendations are divided by urgency.

### Informational level
A public update containing sources, context, and an explanation of what has changed.

### Preventive level
Recommendations to:
- Activate dialogue channels
- Contact mediators
- Protect civilians
- Strengthen humanitarian assistance
- Correct false information
- Support local organisations
- Request independent verification

### Urgent level
A **confidential referral to verified institutions** when there is:
- A credible and imminent risk to civilians
- Rapid escalation
- Attacks against critical infrastructure
- Severe humanitarian obstruction
- Breakdown of a ceasefire
- Risk of regional expansion

The platform never automatically sends instructions to the UN or governments. It generates an **auditable, source-based briefing** routed through authorised institutional contacts.

## 5. AI agent team

Instead of one general chatbot, a team of specialised agents:

| Agent | Role |
|---|---|
| Ingestion agent | Collects data from sources |
| Translation agent | Normalises languages and terminology |
| Verification agent | Compares sources and identifies contradictions |
| Geospatial agent | Locates events and affected populations |
| Conflict analyst | Identifies actors, causes, and trends |
| Humanitarian analyst | Assesses effects on civilians |
| Scenario modeller | Creates conditional scenarios |
| Report writer | Produces alerts and briefings |
| Auditor | Checks citations, bias, and safety |
| Moderator | Manages public contributions |
| Human supervisor | Approves high-risk content |

Agents may use tools for: database searches, graph queries, citation-based document retrieval, version comparison, map generation, report creation, and human-review workflows.

Agents must **not** have direct permission to:
- Publish accusations
- Contact governments
- Influence military operations
- Modify their own safety criteria
