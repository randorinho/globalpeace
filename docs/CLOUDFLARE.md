# Cloudflare Deployment Strategy

The `globalpeace.ai` domain is hosted on Cloudflare. This maps naturally onto the architecture: Cloudflare runs the **edge layer** (site, API gateway, security, caching, light storage), while the heavy stateful stack (PostGIS, Neo4j, OpenSearch, Kafka) runs on origin servers that Cloudflare fronts securely.

## Component mapping

| Architecture component | Cloudflare service | Notes |
|---|---|---|
| Public site + dashboard | **Workers (static assets) / Pages** | React/Next.js; MapLibre tiles cached at the edge |
| Public API gateway | **Workers** | Routing, auth, rate limiting in front of FastAPI origin |
| Raw storage (MinIO/S3) | **R2** | S3-compatible, zero egress fees — good for source snapshots, documents, map tiles |
| Vector search | **Vectorize** (or keep pgvector at origin) | For citation-based RAG at the edge |
| Messaging (light) | **Queues** | Connector fan-out, webhook ingestion buffering; Kafka stays at origin for heavy pipelines |
| Caching / config | **KV** | Source registry, published alert feed, feature flags |
| Postgres access from Workers | **Hyperdrive** | Pooled, accelerated connections to origin PostgreSQL/PostGIS |
| Origin protection | **Tunnel (cloudflared)** | PostGIS/Neo4j/OpenSearch/FastAPI never exposed to the public internet |
| Real-time alerts | **Durable Objects** | WebSocket fan-out for live dashboard updates |
| Edge inference | **Workers AI** | Translation triage, classification of incoming items before origin processing |
| Scheduled ingestion | **Cron Triggers** | Poll RSS/REST sources on schedule, push to Queues |

## Security alignment (maps to GOVERNANCE.md)

Cloudflare directly satisfies several governance requirements:

- **DDoS protection and WAF** — "protection against scraping and denial-of-service attacks"
- **Turnstile** — bot protection on the protected public-contribution forms, without CAPTCHAs harming accessibility
- **Cloudflare Access (Zero Trust)** — MFA + role-based access for the human-review dashboard and confidential briefing channels
- **Bot Management / rate limiting** — defends the public API and source feeds
- **TLS everywhere** — encryption in transit by default

## Recommended split

```
            Cloudflare edge                        Origin (VPS/cloud)
┌──────────────────────────────────┐    ┌────────────────────────────────┐
│ Workers: site, API gateway, auth │    │ FastAPI services               │
│ R2: raw snapshots, documents     │◄──►│ PostgreSQL + PostGIS + pgvector│
│ Queues: webhook/connector buffer │ T  │ Neo4j (actor graph)            │
│ KV: feed cache, source registry  │ u  │ OpenSearch (text search)       │
│ Durable Objects: live alerts     │ n  │ Kafka (heavy pipelines)        │
│ Workers AI: triage/translation   │ n  │ ML models (vLLM)               │
│ Cron Triggers: scheduled polls   │ e  │ Human-review dashboard backend │
│ WAF + Turnstile + Access         │ l  │                                │
└──────────────────────────────────┘    └────────────────────────────────┘
```

## MVP implication

For the 90-day pilot, start with:

1. **Workers + static assets** for the public site and dashboard shell.
2. **Workers API gateway → Tunnel → FastAPI origin** for all data access.
3. **R2** for raw source snapshots from day one (cheap, zero egress).
4. **Turnstile + Access** on contribution forms and the review dashboard.
5. Defer Queues/Vectorize/Durable Objects until the corresponding origin feature exists.
