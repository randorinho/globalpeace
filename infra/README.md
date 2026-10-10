# infra

- **Edge:** the `globalpeace.ai` domain is on Cloudflare — Workers (site + API gateway), R2, Queues, KV, Turnstile, Access, Tunnel. See [docs/CLOUDFLARE.md](../docs/CLOUDFLARE.md).
- **Origin:** docker-compose for PostgreSQL/PostGIS, Neo4j, OpenSearch, Kafka; exposed only through Cloudflare Tunnel.
- **Observability:** OpenTelemetry, Prometheus, Grafana (plus Workers observability on the edge side).
