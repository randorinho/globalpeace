#!/usr/bin/env bash
# Nightly backup: Postgres full dump + Neo4j graph export -> R2 (gpai-backups).
# Registries/audit logs are git-versioned; this covers the databases.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "→ postgres dump"
docker exec gpai-postgres-1 pg_dump -U gpai --format=custom gpai > "$TMP/gpai-$STAMP.pgdump"

echo "→ neo4j export (full graph as cypher-constructable JSON)"
docker exec gpai-neo4j-1 cypher-shell -u neo4j -p gpai-dev-password --format plain \
  "CALL apoc.export.json.all(null, {stream:true}) YIELD data RETURN data" > "$TMP/neo4j-$STAMP.json" 2>/dev/null \
  || docker exec gpai-neo4j-1 cypher-shell -u neo4j -p gpai-dev-password --format plain \
       "MATCH (a)-[r]->(b) RETURN a, type(r) AS rel, properties(r) AS props, b" > "$TMP/neo4j-$STAMP.txt"

echo "→ upload to R2"
cd "$REPO/edge/gateway"
for f in "$TMP"/*; do
  npx wrangler r2 object put "gpai-backups/$(date -u +%Y/%m)/$(basename "$f")" --file "$f" --remote >/dev/null
  echo "  ✓ $(basename "$f") ($(wc -c < "$f" | tr -d ' ') bytes)"
done
echo "✓ backup $STAMP complete"
