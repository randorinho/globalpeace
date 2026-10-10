# pipelines

Ingestion layer: source registry → connectors → classify (transparent rules) → dedupe → events API.

```bash
pip install -e .                       # httpx, feedparser, pyyaml
python -m ingest.run --dry-run         # fetch + classify, post nothing
python -m ingest.run                   # ingest all sources
python -m ingest.run --source reliefweb-sd
```

- `ingest/sources.yaml` — source registry with per-source confidence priors and pilot-country list
- `ingest/connectors/` — `rss` (generic RSS/Atom), `reliefweb` (REST API, no key)
- `ingest/classify.py` — auditable regex rules → event type; unmatched items are skipped and logged, never guessed
- `ingest/dedupe.py` — sqlite ledger in `.state/` so re-runs don't re-post
- Everything lands as `information_type=claim`, `verification_status=unverified` — verification is a separate audited step

Next: wire connectors to Kafka/Redpanda topics and scheduled runs (Cloudflare Cron Triggers → Queues, or local cron).
