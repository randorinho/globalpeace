"""Posts normalised events to the origin API. Ingested items are always
information_type=claim — verification is a separate, audited step."""
import os

import httpx

from .items import RawItem

API_URL = os.environ.get("GPAI_API_URL", "http://localhost:8000")
GATEWAY_SECRET = os.environ.get("GPAI_GATEWAY_SHARED_SECRET", "")


def post_event(item: RawItem, event_type: str, confidence: float) -> dict:
    payload = {
        "date_time": item.published.isoformat(),
        "country": item.country,
        "event_type": event_type,
        "information_type": "claim",
        "source_urls": [item.url],
        "source_language": item.language,
        "confidence": confidence,
        "actors": [],
        "civilian_impact": {},
    }
    headers = {}
    if GATEWAY_SECRET:
        headers["x-gateway-secret"] = GATEWAY_SECRET
    resp = httpx.post(f"{API_URL}/events", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()
