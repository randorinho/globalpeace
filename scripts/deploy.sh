#!/usr/bin/env bash
# globalpeace.ai deploy ritual — main-only, verified end-to-end.
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

echo "→ origin: rebuild API + ensure tunnel"
docker compose -f infra/docker-compose.yml --profile tunnel up -d --build api cloudflared

echo "→ edge: typecheck + deploy Worker"
(cd edge/gateway && npx tsc --noEmit && npx wrangler deploy)

echo "→ verify"
for i in $(seq 1 30); do curl -sf http://localhost:8000/readyz >/dev/null && break; sleep 1; done
curl -sf http://localhost:8000/readyz >/dev/null            && echo "  ✓ origin ready"
curl -sf --max-time 20 https://globalpeace.ai/api/edge-healthz >/dev/null \
                                                             && echo "  ✓ edge healthy"
curl -sf --max-time 30 https://globalpeace.ai/api/public/events >/dev/null \
                                                             && echo "  ✓ public feed through full chain"
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://origin.globalpeace.ai/events)
[[ "$code" == "403" ]] && echo "  ✓ origin rejects unauthenticated access (403)" \
                       || { echo "  ✗ SECURITY: origin returned $code without secret" >&2; exit 1; }
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://globalpeace.ai/api/review/queue)
[[ "$code" == "403" ]] && echo "  ✓ non-public APIs blocked at edge (403)" \
                       || { echo "  ✗ SECURITY: edge returned $code for review API" >&2; exit 1; }
echo "✓ deployed $(git rev-parse --short HEAD) to globalpeace.ai"
