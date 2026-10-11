#!/usr/bin/env bash
# One-time: durable venv for scheduled pipeline runs.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q httpx feedparser pyyaml neo4j anthropic
echo "✓ .venv ready ($(.venv/bin/python --version))"
