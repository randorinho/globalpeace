#!/usr/bin/env bash
# Provision the gpai origin VPS on Hetzner Cloud.
# Needs HCLOUD_TOKEN in infra/.env (Read & Write project token).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
set -a; source "$REPO/infra/.env"; set +a
: "${HCLOUD_TOKEN:?add HCLOUD_TOKEN=... to infra/.env (Hetzner Cloud project API token)}"

NAME=gpai-origin
TYPE=${GPAI_VPS_TYPE:-cx32}        # 4 vCPU / 8 GB
LOCATION=${GPAI_VPS_LOCATION:-nbg1}
IMAGE=ubuntu-24.04

if ! [ -f "$HOME/.ssh/id_ed25519.pub" ]; then
  ssh-keygen -t ed25519 -N "" -f "$HOME/.ssh/id_ed25519"
fi
hcloud ssh-key describe gpai-operator >/dev/null 2>&1 \
  || hcloud ssh-key create --name gpai-operator --public-key-from-file "$HOME/.ssh/id_ed25519.pub"

# Inbound: SSH only. The web path is the outbound cloudflared tunnel.
hcloud firewall describe gpai-fw >/dev/null 2>&1 || {
  hcloud firewall create --name gpai-fw
  hcloud firewall add-rule gpai-fw --direction in --protocol tcp --port 22 --source-ips 0.0.0.0/0 --source-ips ::/0
}

hcloud server describe $NAME >/dev/null 2>&1 || hcloud server create \
  --name $NAME --type $TYPE --location $LOCATION --image $IMAGE \
  --ssh-key gpai-operator --firewall gpai-fw \
  --user-data-from-file "$REPO/infra/cloud-init.yml"

IP=$(hcloud server ip $NAME)
echo "✓ $NAME ready at $IP (SSH only; web egress via tunnel)"
echo "$IP" > "$REPO/infra/.vps_ip"
