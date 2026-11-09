# gpai-gateway

Cloudflare Worker — the entire public surface of globalpeace.ai
(docs/DARK_ORIGIN.md): static frontend assets, basemap proxy, /api/public/*
reads from published snapshots (R2 bucket gpai-public), the contributions
buffer (D1 gpai-edge), and the gateway-secret-authenticated /api/internal/*
drain routes the origin calls outbound. There is no path from the edge to
the origin.

```bash
npm install
npm run types     # generates worker-configuration.d.ts (Env) from wrangler.jsonc
npm run check     # tsc --noEmit
npm run dev       # local dev (local R2/D1 simulations; seed via wrangler --local)
wrangler secret put GATEWAY_SHARED_SECRET   # authenticates the origin's drain calls
npm run deploy
```

`.dev.vars` (gitignored) for local dev:

```
GATEWAY_SHARED_SECRET=dev-only-change-me
```
