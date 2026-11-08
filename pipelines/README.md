# pipelines

Ingestion layer: source registry → connectors → classify (transparent rules) → dedupe → events API.

```bash
pip install -e .                       # httpx, feedparser, pyyaml
python -m ingest.run --dry-run         # fetch + classify, post nothing
python -m ingest.run                   # ingest all sources
python -m ingest.run --source reliefweb-sd
```

- `ingest/sources.yaml` — source registry with per-source confidence priors
- `ingest/countries.py` — full ISO-3166 registry; name→country matching is word-boundary based and longest-alias-first (unmatched items are skipped and logged, never guessed)
- `ingest/connectors/` — `rss` (generic RSS/Atom, retries ReliefWeb's WAF 202s), `reliefweb` (REST API; global mode attributes by structured `primary_country.iso3`, needs registered RELIEFWEB_APPNAME), `ucdp` (UCDP GED releases; needs registered UCDP_API_TOKEN, 5,000 req/day — each immutable release is walked once, then skipped via a `.state/` marker)
- `ingest/classify.py` — auditable regex rules → event type; unmatched items are skipped and logged, never guessed
- `ingest/dedupe.py` — sqlite ledger in `.state/` so re-runs don't re-post
- Everything lands as `information_type=claim`, `verification_status=unverified` — verification is a separate audited step
- `publish/` — dark-origin snapshot publisher (docs/DARK_ORIGIN.md): mirrors every public API payload to the R2 bucket the edge worker serves (`python -m publish.run`, `--dry-run`, `--verify`); incremental via `.state/snapshots.json`; uploads over the S3 API (`R2_ENDPOINT`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` in infra/.env) or an authenticated wrangler as fallback, and skips harmlessly with neither

Next: wire connectors to Kafka/Redpanda topics and scheduled runs (Cloudflare Cron Triggers → Queues, or local cron).
