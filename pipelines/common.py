"""Shared pipeline config: origin API access with the gateway shared secret
(read from env or infra/.env — the pipelines are trusted local callers)."""
import os
import re
from pathlib import Path

API_URL = os.environ.get("GPAI_API_URL", "http://localhost:8000")


def gateway_secret() -> str:
    if s := os.environ.get("GPAI_GATEWAY_SHARED_SECRET"):
        return s
    env_file = Path(__file__).parent.parent / "infra" / ".env"
    if env_file.exists():
        if m := re.search(r"GPAI_GATEWAY_SHARED_SECRET=(.+)", env_file.read_text()):
            return m.group(1).strip()
    return ""


def api_headers() -> dict[str, str]:
    s = gateway_secret()
    return {"x-gateway-secret": s} if s else {}
