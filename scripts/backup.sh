#!/usr/bin/env bash
# Nightly backup: Postgres full dump + Neo4j graph export.
# Keeps local copies under BACKUP_DIR with rotation, then copies off-site to
# R2 (bucket gpai-backups) when an rclone remote named "r2" is configured.
# Registries/audit logs are git-versioned; this covers the databases.
# Installed on the origin as a systemd timer (gpai-backup.timer, 03:30 UTC).
set -uo pipefail
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
if [[ "$(uname)" == "Darwin" ]]; then DEFAULT_DIR="$HOME/Backups/gpai"; else DEFAULT_DIR="/var/backups/gpai"; fi
BACKUP_DIR="${GPAI_BACKUP_DIR:-$DEFAULT_DIR}"
RETENTION_DAYS="${GPAI_BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$BACKUP_DIR"

echo "→ postgres dump"
docker exec gpai-postgres-1 pg_dump -U gpai --format=custom gpai > "$BACKUP_DIR/gpai-$STAMP.pgdump" \
  || { echo "✗ postgres dump failed" >&2; exit 1; }

echo "→ neo4j export"
docker exec gpai-neo4j-1 cypher-shell -u neo4j -p gpai-dev-password --format plain \
  "CALL apoc.export.json.all(null, {stream:true}) YIELD data RETURN data" > "$BACKUP_DIR/neo4j-$STAMP.json" 2>/dev/null \
  || docker exec gpai-neo4j-1 cypher-shell -u neo4j -p gpai-dev-password --format plain \
       "MATCH (a)-[r]->(b) RETURN a, type(r) AS rel, properties(r) AS props, b" > "$BACKUP_DIR/neo4j-$STAMP.txt" \
  || echo "  neo4j export failed (graph may be empty) — continuing" >&2

echo "→ rotate (> $RETENTION_DAYS days)"
find "$BACKUP_DIR" -type f -mtime +"$RETENTION_DAYS" -delete

# Off-site copy. Configure once:  rclone config create r2 s3 provider=Cloudflare \
#   access_key_id=... secret_access_key=... endpoint=https://<account_id>.r2.cloudflarestorage.com
if command -v rclone >/dev/null 2>&1 && rclone listremotes 2>/dev/null | grep -q '^r2:'; then
  echo "→ off-site to R2 (gpai-backups)"
  rclone copy "$BACKUP_DIR" "r2:gpai-backups/$(date -u +%Y/%m)/" \
    --include "*${STAMP}*" && echo "  ✓ off-site complete" || echo "  ✗ off-site FAILED" >&2
else
  echo "→ off-site skipped: rclone remote 'r2' not configured (local copies only)"
fi

ls -lh "$BACKUP_DIR" | tail -3
echo "✓ backup $STAMP complete ($(ls "$BACKUP_DIR" | wc -l | tr -d ' ') file(s) retained)"
