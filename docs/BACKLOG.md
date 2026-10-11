# Internal Backlog

Mission anchor: the competitive advantage is **promoting peace** — machine
power generates and promotes solutions at scale; a named human remains the
accountable signature on every outbound action (docs/GOVERNANCE.md;
docs/references/apdsi-un-charter-reform.md, Art. 86-C). AI proposes, humans
dispose, the system keeps receipts.

Status markers: `[ ]` todo · `[~]` partial · `[x]` done (kept for context).

---

## P0 — Operational trust (do first)

The platform is live at globalpeace.ai; these make it dependable.

- [ ] **Migrate origin off the laptop** — VPS or small cloud box running the
      compose stack + tunnel; laptop closing currently takes the data layer down
- [ ] **Alembic migrations** — replace startup `create_all` + manual `ALTER TABLE`
- [ ] **Deploy guard** — `deploy.sh` that refuses to run off `main`
      (compose rebuild + `wrangler deploy` as one ritual); branch flow is dev → main
- [ ] **Scheduled pipeline runs** — ingestion every 30 min, audit after each
      ingest run (cron/launchd now; Cloudflare Cron Triggers + Queues later)
- [ ] **Anthropic API credentials on the pipeline host** — activates the six
      continental audit desks (code shipped, degrades to rules-only today)
- [ ] **Cloudflare Access on review APIs** — reviewer login via Access,
      identity from `cf-access-authenticated-user-email`; then open
      `/api/review/*` at the edge for remote reviewers
- [ ] **Backups** — nightly `pg_dump` + Neo4j dump, copies to R2
- [ ] **Monitoring** — uptime checks on edge + origin health; alert on tunnel drop
- [x] Workers gateway + Tunnel live; origin secret-gated; public allowlist at edge

## P1 — Intelligence depth

- [ ] **ACLED connector** — register for API access; conflict-event ingestion +
      the cross-check target the audit matrix already names
- [ ] **UNHCR data portal connector** — refugee/displacement figures
      (the other named cross-check primary)
- [ ] **Source expansion** — remaining pilot countries (SS, CD, HT feeds),
      local-language/independent outlets per region
- [ ] **Geolocation extraction** — place names → coordinates with explicit
      precision flags (country/admin1/exact); map already renders the distinction
- [ ] **Server-side dedupe** — unique index on source URL; drop reliance on the
      local sqlite ledger
- [ ] **Country pages + timeline** — remaining MVP deliverables (docs/ROADMAP.md)
- [ ] **Load real SIPRI export** — connector shipped; needs the portal CSV;
      UNROCA connector as second arms-data source
- [~] Actor graph — Neo4j live with SUPPLIED edges; next: conflict parties,
      mediators, humanitarian-access relationships from reviewed events

## P2 — Solutions Engine (the differentiator)

Everything here produces `recommendation`-type information (docs/DATA_MODEL.md):
drafted by machine, dispatched by an accountable human, auditable end to end.

- [ ] **Situation clustering** — group reviewed events into situations
      (country + period + theme) as the unit solutions attach to
- [ ] **Solution generator** — per situation, AI drafts preventive options from
      the playbook in docs/ARCHITECTURE.md (activate dialogue channels, mediator
      contacts, civilian protection, humanitarian assistance, disinformation
      correction, local-organisation support) — every option carries cited
      evidence, confidence, and what would make it wrong
- [ ] **Scenario modeller** — conditional scenarios with explicit uncertainty;
      never rendered as forecasts of fact
- [ ] **Briefing generator** — auditable, source-linked briefing documents for
      institutional contacts (informational / preventive / urgent levels)
- [ ] **Dispatch workflow** — reviewer approves a drafted solution → routed to a
      maintained registry of verified institutional contacts; append-only
      dispatch log (who approved, what, to whom, when)
- [ ] **Outcome tracking** — record which recommendations were acted on and
      what changed; the feedback loop that proves impact
- [ ] **Mediator/contact registry** — vetted organisations per region, with
      consent and channel preferences

## P3 — Scale & community

- [ ] **Contribution moderation queue UI** — triage view across all public
      submissions (per-event view shipped)
- [ ] **Multilingual UI + validated translation** for critical content
- [ ] **Edge caching** — public feed in KV; rate limiting at the Worker
- [ ] **Actor-graph explorer UI** — relationships view per docs/DATA_MODEL.md
      (evidence + uncertainty, never rankings)
- [ ] **Institutional model** — publish methodology; scientific/peace council
      structure; annual external audit plan (docs/GOVERNANCE.md)

## Development environment (DevEx)

- [ ] **GitHub remote + CI** — push the repo; Actions running `tsc --noEmit`,
      frontend build, backend import check, pipeline unit tests on PRs to dev/main
- [ ] **Test suites** — pytest for API (review/evidence/audit invariants are the
      crown jewels: retraction gate, claim→fact only via verified, honeypot),
      parser tests (ingest, SIPRI fixture), vitest for frontend
- [ ] **Pre-commit hooks** — ruff + eslint/prettier
- [ ] **Task runner** — `justfile`/Makefile: `just up`, `just ingest`,
      `just audit`, `just deploy`
- [ ] **Staging environment** — second Worker env (`env.staging`) +
      `origin-staging` tunnel hostname
- [ ] **Secrets documentation** — what lives where (wrangler secrets,
      infra/.env, tunnel credentials), rotation steps
- [x] dev/main branch flow; secrets gitignored and verified out of history
