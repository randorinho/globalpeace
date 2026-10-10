# gpai-gateway

Cloudflare Worker fronting the FastAPI origin (via Cloudflare Tunnel).

```bash
npm install
npm run types     # generates worker-configuration.d.ts (Env) from wrangler.jsonc
npm run check     # tsc --noEmit
npm run dev       # local dev (set ORIGIN_URL to http://localhost:8000 in .dev.vars)
wrangler secret put GATEWAY_SHARED_SECRET
wrangler secret put CF_ACCESS_CLIENT_ID
wrangler secret put CF_ACCESS_CLIENT_SECRET
npm run deploy
```

`.dev.vars` (gitignored) for local dev:

```
ORIGIN_URL=http://localhost:8000
GATEWAY_SHARED_SECRET=dev-only-change-me
```
