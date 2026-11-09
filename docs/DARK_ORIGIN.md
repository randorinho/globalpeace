# Dark origin — implementation plan

Security-by-design decision (2026-11-08): the origin (FastAPI + Postgres +
Neo4j + the pipelines) becomes unreachable from the internet. The public site
is served entirely from the edge: static frontend assets plus **published data
snapshots**. Every remaining flow is **outbound from the origin** — there is no
inbound path at all, not even a tunnel.

## Why

Public data changes on the pipeline cadence (ingest every 30 min, agent stages
once a day), yet today every visitor request travels worker → Cloudflare
Tunnel → FastAPI → Postgres/Neo4j, 24/7. Serving snapshots instead:

- collapses the attack surface to Cloudflare's edge + static objects — an
  exploitable bug in FastAPI/SQLAlchemy/the graph driver becomes unreachable;
- makes the site independent of origin uptime (origin-down twice this week
  meant site-API-down; with snapshots it means "data pauses", visibly);
- keeps visitor IPs and query patterns off the origin entirely (same reasoning
  as the D15 map-tile proxy, extended to the whole data plane);
- turns scraping/abuse into a CDN-cache problem instead of a database problem.

## Target architecture

```
visitor ──► Cloudflare Worker (gpai-gateway)
              ├─ /            static SPA assets (as today)
              ├─ /map/*       tile proxy (as today)
              ├─ /api/public/* GET   ──► R2 snapshot objects
              ├─ /api/public/contributions POST ──► edge buffer (D1)
              └─ anything else: 403/404 at the edge

origin (docker compose, zero inbound ports, no tunnel)
              ├─ pipelines run as today against localhost:8000
              ├─ snapshot publisher ──► R2 (outbound, S3 API)        [new]
              └─ contribution drain ──► worker /api/internal/* (outbound) [new]
```

The Cloudflare Tunnel is **removed**, not just gated: once reads come from R2
and contribution drain is origin-initiated, nothing needs worker→origin.
The review console keeps working unchanged — it is the local vite dev server
proxying to localhost:8000 and never traverses the edge.

## Snapshot set (R2 bucket `gpai-public`)

| key | source endpoint | notes |
|---|---|---|
| `public/events.json` | `/public/events?limit=2000` | one canonical file; the worker ignores `limit` (UI slices client-side) |
| `public/events.geojson` | `/public/events.geojson` | open-data export |
| `public/events.csv` | `/public/events.csv` | open-data export |
| `public/arms-transfers.json` | `/public/arms-transfers?limit=1000` | global |
| `public/arms-transfers/<ISO2>.json` | `/public/arms-transfers?country=XX` | per-country (Country pages) |
| `public/hra/position.json` + `positions.json` | `/public/hra/*` | |
| `public/solutions.json` + `solutions/history.json` | `/public/solutions*` | |
| `public/trails/<event_id>.json` | `/public/events/{id}/trail` | only for currently-published events |
| `public/meta.json` | generated | `generated_at`, counts, pipeline commit — the staleness signal |

Incremental publish: the publisher keeps a local manifest of content hashes
(`pipelines/.state/snapshots.json`) and PUTs only changed keys — trails for
thousands of events must not mean thousands of writes per cycle. Keys for
events that leave the published set are deleted (publish/remove symmetry).

## Phases

### Phase 1 — publisher + snapshot reads (no behavior change on failure) ✅ 2026-11-09

Ownership: the PRODUCTION origin (the VPS at /opt/gpai) publishes; any other
copy sets GPAI_EDGE_SYNC_DISABLED=1 (the reviewer laptop does) so dev data
can never overwrite production's snapshots — learned the hard way on 11-08.

1. `pipelines/publish/run.py`: queries localhost:8000 for each payload above,
   diffs against the manifest, uploads changed keys to R2 (boto3, S3 API;
   `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`/`R2_BUCKET` in `infra/.env`).
   Wired as the last stage of `scripts/run_pipelines.sh`.
2. Worker: R2 binding; `GET /api/public/*` maps path+country param → object
   key, served with `etag` + `cache-control: public, max-age=300` and edge
   cache. **Fallback to the origin proxy when the object is missing** so the
   cutover is reversible request-by-request.
3. Frontend: footer shows `data as of <meta.generated_at>` (staleness must be
   visible, per GOVERNANCE's "coverage gaps are never silent").

Acceptance: diff snapshot responses against live origin responses for every
endpoint; zero differences for a full pipeline day.

### Phase 2 — contributions at the edge ✅ 2026-11-09 (verified live: edge buffer → VPS drain → moderation queue)

1. D1 table `pending_contributions(id, event_id, text, url, created_at,
   client_hash)`. The worker's POST handler enforces what the origin enforces
   today: size caps, honeypot, 5/hour per hashed `cf-connecting-ip` (hash at
   the edge, raw IP never stored — same data-minimisation stance). The PII
   regex screen runs at the edge too, but the canonical screen re-runs at
   drain time — transparent rules stay in Python where they're tested.
2. Worker route `POST /api/internal/contributions/drain`, authenticated with
   `GATEWAY_SHARED_SECRET` (already shared by both sides): returns pending
   rows and deletes them on acknowledged receipt. A drain step in
   `run_pipelines.sh` calls it and inserts into Postgres as today (enters the
   same human-review queue; nothing auto-incorporated).
3. `event_id` referential check moves to drain time (the edge can't see the
   events table; a dangling reference becomes a drain-time reject, logged).

Acceptance: submission on the live site lands in the review console after the
next pipeline window; rate limit and PII screen behave as before.

### Phase 3 — go dark ✅ 2026-11-09

1. Flip the worker: `/api/public/*` reads are R2-only (origin fallback
   removed); `/api/*` everything else answers 403/404 at the edge.
   `/api/healthz` passthrough is removed — monitoring switches to
   `meta.json` freshness (alert when `generated_at` > 36 h) plus
   `/api/edge-healthz`, both in `.github/workflows/uptime.yml`.
2. Stop and remove the `cloudflared` service from `infra/docker-compose.yml`;
   delete the tunnel and the `origin.globalpeace.ai` DNS record; revoke the
   tunnel credential (`infra/cloudflared/*.json`) and the Access service
   token if one was issued.
3. Rotate `GATEWAY_SHARED_SECRET` (its role shrinks to authenticating the
   drain call) and delete `ORIGIN_URL` from `wrangler.jsonc`.

Acceptance: external scan shows no inbound path to the origin host; site fully
functional with the compose stack stopped; a pipeline window updates the site.

Verified live 2026-11-09: snapshots serve all public reads (x-gpai-snapshot),
healthz and non-public API closed at the edge, cloudflared removed from the
VPS (origin.globalpeace.ai answers 530 — no connector), GATEWAY_SHARED_SECRET
rotated on worker/VPS/laptop with the drain re-authenticated. Outstanding
hygiene: delete the tunnel object + origin DNS record in the dashboard and
remove the credential files from both machines.

### Phase 4 — write it down ✅ 2026-11-09 (docs/SECURITY.md + weekly dependency audit; ARCHITECTURE/privacy-page updates with the DPO desk)

- `docs/SECURITY.md`: the invariants this plan establishes — *origin accepts
  no inbound connections; public data is published, never queried; the only
  write path is buffered, rate-limited and human-reviewed; secrets live in
  `infra/.env`/wrangler secrets, never the repo* — plus the self-assessment
  checks that verify each invariant from outside.
- Update `docs/ARCHITECTURE.md` (data plane) and `docs/PRIVACY` surface if
  the DPO wants the "visitor data never reaches the backend" claim published.
- BACKLOG: close the tunnel/Access hardening items this supersedes.

## Open questions (decide before phase 2/3)

- **Rate-limit state**: KV TTL counters are eventually consistent (a burst can
  exceed 5/h briefly). Accept, or use a Durable Object for exact counting?
  Proposed: accept KV-level approximation; the honeypot and review queue are
  the real gates.
- **Snapshot growth**: `events.json` at 2k events is ~1–2 MB; if the published
  set grows past that, switch Country pages to per-country event files
  (`public/events/<ISO2>.json`) — the publisher layout already allows it.
- **Emergency access**: with the tunnel gone, operator access to the origin
  host is SSH only (as provisioned). Confirm that's acceptable before
  deleting the tunnel rather than merely stopping it.

## Effort

Phase 1 ≈ one working session (publisher + worker read path + diff test).
Phase 2 ≈ one session (D1 schema, edge checks, drain). Phase 3 ≈ half a
session plus a cooling-off day watching the fallback counters. Phase 4 ≈ docs.
