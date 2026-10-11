#!/usr/bin/env bash
# Scheduled pipeline run: ingest sources, then audit new events.
# Invoked by launchd every 30 min (infra/launchd/). Safe to run manually.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$REPO/.pipeline.lock"
LOG_DIR="$HOME/Library/Logs/gpai"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/pipelines-$(date +%Y%m%d).log"

# single-flight: skip if a previous run is still going (stale after 1h)
if ! mkdir "$LOCK" 2>/dev/null; then
  if [[ -n "$(find "$LOCK" -maxdepth 0 -mmin +60 2>/dev/null)" ]]; then rmdir "$LOCK"; mkdir "$LOCK" || exit 0
  else echo "$(date -u +%FT%TZ) skipped: previous run in flight" >> "$LOG"; exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# load platform secrets (gateway secret, ANTHROPIC_API_KEY for the audit desks)
if [[ -f "$REPO/infra/.env" ]]; then set -a; source "$REPO/infra/.env"; set +a; fi

PY="$REPO/.venv/bin/python"
[[ -x "$PY" ]] || { echo "$(date -u +%FT%TZ) ERROR: .venv missing — run scripts/setup_venv.sh" >> "$LOG"; exit 1; }

{
  echo "=== $(date -u +%FT%TZ) run start (commit $(git -C "$REPO" rev-parse --short HEAD))"
  # origin must be up; skip quietly if the stack is down (e.g. laptop just woke)
  if ! curl -sf --max-time 10 http://localhost:8000/readyz >/dev/null; then
    echo "origin not ready — skipping this cycle"; exit 0
  fi
  cd "$REPO/pipelines"
  echo "--- ingest"
  "$PY" -m ingest.run 2>&1
  echo "--- audit (continental desks; degrades to rules without API key)"
  "$PY" -m audit.run --with-desks 2>&1
  echo "--- human rights agent (vitals + dev audit + published position)"
  "$PY" -m hra.run 2>&1
  echo "--- solutions engine (political + economic approaches per situation)"
  "$PY" -m solutions.run 2>&1
  echo "=== run end $(date -u +%FT%TZ)"
} >> "$LOG" 2>&1
