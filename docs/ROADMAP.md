# Roadmap — 90-Day MVP Pilot

Do not begin with every country and every conflict. Build a 90-day pilot covering:

## Scope

- 3–5 regions
- 5–10 languages
- 10–20 verified sources
- ACLED, UN, humanitarian, and news data

## Deliverables

- An event map
- A country page
- A timeline
- A basic actor graph
- Source-based alerts
- A correction system
- Mandatory human review
- A weekly quality report

## First functional stack

```
PostgreSQL/PostGIS
+ OpenSearch
+ Neo4j
+ Python/FastAPI
+ Kafka or Redis Streams
+ React/MapLibre
+ multilingual language model
+ citation-based RAG
+ human-review dashboard
```

## Success criteria

The first objective is **not** to "predict every war." It is to demonstrate that the system can:

1. Detect a relevant change.
2. Confirm it through independent sources.
3. Explain the context.
4. Show who is affected.
5. Indicate uncertainty.
6. Suggest proportionate civil and diplomatic responses.
7. Avoid causing additional harm.
