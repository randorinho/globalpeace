#!/usr/bin/env bash
# globalpeace.ai deploy ritual — main-only, verified end-to-end.
# Dark origin (docs/DARK_ORIGIN.md): no tunnel, no public origin host.
# Usage: scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

branch=$(git branch --show-current)
if [[ "$branch" != "main" ]]; then
  echo "✗ deploys run from main only (current: $branch)." >&2
  echo "  Merge dev → main first: git switch main && git merge dev" >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "✗ working tree not clean — commit or stash first." >&2
  exit 1
fi

echo "→ origin: pull + rebuild API (loopback-only; never publicly reachable)"
if [[ -f infra/.vps_ip ]]; then
  VPS_IP=$(cat infra/.vps_ip)
  ssh root@"$VPS_IP" "cd /opt/gpai && git pull -q && docker compose -f infra/docker-compose.yml up -d --build --remove-orphans api"
else
  docker compose -f infra/docker-compose.yml up -d --build --remove-orphans api
fi

echo "→ frontend: build static assets"
(cd frontend && npm ci --no-fund --no-audit >/dev/null 2>&1 || npm install --no-fund --no-audit >/dev/null; npm run build)

echo "→ edge: typecheck + deploy Worker"
(cd edge/gateway && npx tsc --noEmit && npx wrangler deploy)

echo "→ verify"
if [[ -f infra/.vps_ip ]]; then
  ready() { ssh root@"$(cat infra/.vps_ip)" "curl -sf http://localhost:8000/readyz" >/dev/null; }
else
  ready() { curl -sf http://localhost:8000/readyz >/dev/null; }
fi
for i in $(seq 1 30); do ready && break; sleep 1; done
ready                                                       && echo "  ✓ origin ready (loopback)"
curl -sf --max-time 20 https://globalpeace.ai/api/edge-healthz >/dev/null \
                                                             && echo "  ✓ edge healthy"
curl -sf --max-time 30 https://globalpeace.ai/api/public/events >/dev/null \
                                                             && echo "  ✓ public feed from snapshots"
curl -sf --max-time 20 https://globalpeace.ai/ | grep -q globalpeace && echo "  ✓ frontend served at zone root"
if curl -sf --max-time 15 https://origin.globalpeace.ai/healthz >/dev/null 2>&1; then
  echo "  ✗ SECURITY: origin is publicly reachable — it must be dark" >&2; exit 1
else
  echo "  ✓ origin is dark (no public route)"
fi
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://globalpeace.ai/api/review/queue)
[[ "$code" == "403" ]] && echo "  ✓ non-public APIs blocked at edge (403)" \
                       || { echo "  ✗ SECURITY: edge returned $code for review API" >&2; exit 1; }
echo "✓ deployed $(git rev-parse --short HEAD) to globalpeace.ai"
