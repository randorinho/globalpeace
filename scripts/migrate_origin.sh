#!/usr/bin/env bash
# Migrate the origin stack from this machine to the provisioned VPS.
# Fresh backup -> clone public repo on VPS -> transfer secrets -> restore DB
# -> start stack + tunnel -> systemd timer for pipelines -> verify -> cut over.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
IP=${1:-$(cat "$REPO/infra/.vps_ip")}
SSH="ssh -o StrictHostKeyChecking=accept-new root@$IP"

echo "→ 1/7 fresh backup"
bash "$REPO/scripts/backup.sh" >/dev/null
DUMP=$(docker exec gpai-postgres-1 pg_dump -U gpai --format=custom gpai | base64 | wc -c >/dev/null; mktemp)
docker exec gpai-postgres-1 pg_dump -U gpai --format=custom gpai > "$DUMP"

echo "→ 2/7 clone repo on VPS"
$SSH "test -d /opt/gpai || git clone https://github.com/randorinho/globalpeace /opt/gpai; cd /opt/gpai && git switch main && git pull -q"

echo "→ 3/7 transfer secrets (never in git)"
# Dark origin (docs/DARK_ORIGIN.md): no tunnel credentials exist anymore.
# Mind GPAI_EDGE_SYNC_DISABLED: it must be ABSENT on the production copy.
scp -q "$REPO/infra/.env" root@$IP:/opt/gpai/infra/.env
$SSH "chmod 600 /opt/gpai/infra/.env && sed -i '/^GPAI_EDGE_SYNC_DISABLED=/d' /opt/gpai/infra/.env"
scp -q "$DUMP" root@$IP:/opt/gpai/restore.pgdump && rm -f "$DUMP"

echo "→ 4/7 start data stores and restore"
$SSH "cd /opt/gpai/infra && docker compose up -d postgres neo4j opensearch redpanda"
$SSH "cd /opt/gpai/infra && until docker exec gpai-postgres-1 pg_isready -U gpai >/dev/null 2>&1; do sleep 2; done"
$SSH "docker exec -i gpai-postgres-1 pg_restore -U gpai --clean --if-exists -d gpai < /opt/gpai/restore.pgdump && rm /opt/gpai/restore.pgdump"

echo "→ 5/7 start API (loopback-only; the edge serves snapshots, never this host)"
$SSH "cd /opt/gpai/infra && docker compose up -d --build --remove-orphans api"

echo "→ 6/7 pipelines on VPS (systemd timer, 30 min)"
$SSH "cd /opt/gpai && bash scripts/setup_venv.sh"
$SSH 'cat > /etc/systemd/system/gpai-pipelines.service <<UNIT
[Unit]
Description=gpai pipelines (ingest, audit, HRA, solutions)
[Service]
Type=oneshot
WorkingDirectory=/opt/gpai
ExecStart=/bin/bash /opt/gpai/scripts/run_pipelines.sh
UNIT
cat > /etc/systemd/system/gpai-pipelines.timer <<UNIT
[Unit]
Description=gpai pipelines every 30 min
[Timer]
OnBootSec=3min
OnUnitActiveSec=30min
[Install]
WantedBy=timers.target
UNIT
cat > /etc/systemd/system/gpai-backup.service <<UNIT
[Unit]
Description=gpai nightly backup to R2
[Service]
Type=oneshot
WorkingDirectory=/opt/gpai
ExecStart=/bin/bash /opt/gpai/scripts/backup.sh
UNIT
cat > /etc/systemd/system/gpai-backup.timer <<UNIT
[Unit]
Description=gpai nightly backup
[Timer]
OnCalendar=*-*-* 03:15:00 UTC
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload && systemctl enable --now gpai-pipelines.timer gpai-backup.timer'

echo "→ 7/7 verify (the public site never depends on this host being up)"
$SSH "curl -sf --max-time 20 http://localhost:8000/readyz" && echo "  ✓ VPS origin ready (loopback)"
$SSH "cd /opt/gpai && set -a; . infra/.env; set +a; cd pipelines && ../.venv/bin/python -m publish.run" \
  && echo "  ✓ VPS published snapshots"
curl -sf --max-time 30 https://globalpeace.ai/api/public/events >/dev/null && echo "  ✓ public feed from snapshots"
echo "→ stopping laptop pipeline schedule (VPS systemd timer owns it now)"
launchctl bootout gui/$(id -u)/ai.globalpeace.pipelines 2>/dev/null || true
echo "  ✓ migration complete — set GPAI_EDGE_SYNC_DISABLED=1 in the laptop infra/.env if it keeps a dev stack"
