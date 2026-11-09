# Security — invariants and self-assessment

Security here is architectural (docs/DARK_ORIGIN.md): the public surface is a
Cloudflare Worker serving static assets and published snapshots; the origin
makes outbound calls only. This document states the invariants that design
establishes, how each one is verified, and the cadence for checking them.
Last full verification: 2026-11-09.

## Trust boundaries

```
internet ──► Cloudflare edge (worker gpai-gateway)
               static SPA · /map tile proxy · /api/public/* ← R2 snapshots
               POST /api/public/contributions → D1 buffer
               /api/internal/* (gateway-secret) ← called OUTBOUND by origin
internet ──► origin host: SSH only (key auth)

origin (VPS /opt/gpai, docker compose, all service ports loopback-bound)
  outbound: snapshot publish → R2 · drain → worker · source APIs · Anthropic
reviewer laptop: same stack for review/dev; GPAI_EDGE_SYNC_DISABLED=1
```

## Invariants

1. **The origin accepts no inbound connections except SSH.** No tunnel, no
   reverse proxy, no port mappings beyond loopback. *Verified:* `ss -tlnp`
   non-loopback shows only sshd; external probe gets no service response
   (Hetzner's DDoS SYN-proxy answers handshakes on any port — ignore
   nc/nmap "open" results, test for actual service banners).
2. **Public data is published, never queried.** Every `/api/public/*` read is
   a snapshot object; the worker has no code path to the origin. Staleness is
   visible (`/api/public/meta`, footer timestamp) and alarmed (uptime fails
   at >36 h). *Verified:* `x-gpai-snapshot: 1` on responses; uptime probe.
3. **The only public write is buffered, validated, rate-limited, and
   human-reviewed.** Contributions: honeypot, size caps, PII screen and an
   exact 5/hour/client-hash limit at the edge; canonical Python screens
   re-run at drain; nothing is ever auto-incorporated (docs/GOVERNANCE.md).
4. **Non-public API surfaces end at the edge** with 403/405/404 —
   review/ingest/audit/evidence endpoints are unreachable from the internet.
   *Verified:* uptime probe asserts 403 on `/api/events` every 15 min.
5. **Secrets never live in the repo** (it is public). They live in
   `infra/.env` (mode 600) and wrangler secrets. Every credential has one
   purpose and minimal scope (inventory below).
6. **Non-production copies cannot write production surfaces.**
   `GPAI_EDGE_SYNC_DISABLED=1` on every copy except the VPS blocks snapshot
   publishing and draining. (Added after the 2026-11-08 incident where the
   reviewer laptop published its dev data over production's snapshots.)
7. **Visitor data is minimised.** Raw IPs are never stored (hashed at the
   edge for rate limiting only); basemap traffic is proxied so the tile host
   never sees visitors (DPO D15); origin never sees visitor traffic at all.

## Credential inventory

| secret | lives in | scope / purpose | rotate |
|---|---|---|---|
| `GATEWAY_SHARED_SECRET` | wrangler secret + both `infra/.env` | authenticates origin's drain calls to `/api/internal/*` | rotated 2026-11-09; yearly or on suspicion |
| `gpai-public-publisher` (R2 S3) | both `infra/.env` (`R2_ENDPOINT/ACCESS_KEY_ID/SECRET_ACCESS_KEY`) | Object R/W on bucket `gpai-public` only | dashboard → R2 → API tokens |
| backups token (R2 S3) | both `infra/.env` (`R2_BACKUPS_*`) | Object R/W on bucket `gpai-backups` only | idem |
| `UCDP_API_TOKEN` | both `infra/.env` | UCDP API reads, 5k req/day | email UCDP |
| `ANTHROPIC_API_KEY` | both `infra/.env` | audit/HRA/solutions LLM calls (budget-capped, pipelines/llm_budget.py) | console.anthropic.com |
| `HCLOUD_TOKEN` | laptop `infra/.env` | Hetzner provisioning | Hetzner console |
| SSH key | operator machines | only inbound path to the origin host | on operator change |

## Self-assessment

**Every 15 minutes** (`.github/workflows/uptime.yml`): edge health; public
feed end-to-end; snapshot freshness (<36 h); non-public API answers 403;
origin host serves nothing publicly (probe must fail).

**Weekly** (`.github/workflows/security.yml`): dependency audit — `pip-audit`
over the pipelines/backend requirements and `npm audit` (high+) over the
worker and frontend.

**Quarterly, by hand** (S desk checklist):
- `ss -tlnp` on the VPS: nothing non-loopback but sshd.
- Service-banner probe of the VPS IP from outside (not nc/nmap alone).
- Token scopes unchanged in the Cloudflare dashboard; delete unknowns.
- CT-log check for unexpected certificates on globalpeace.ai.
- `infra/.env` mode 600 on both machines; no secrets in `git log -p` since
  the last check (`git log -S` for key fragments).
- D1 buffer: drained rows purge (>25 h) actually happening.
- Restore one backup into a scratch database (backups that never restored
  are hope, not backups).

## Incident basics

Credential suspected leaked → rotate at its issuer (table above), update both
`infra/.env`, `docker compose up -d api` on the VPS, and for the gateway
secret also `wrangler secret put`. Origin host suspected compromised → it
holds no inbound path to the edge: rotate the drain secret and the R2 tokens,
rebuild the VPS from `infra/cloud-init.yml` + latest backup. Edge worker
suspected compromised → `wrangler rollback`, then audit `wrangler deployments
list` authorship.
