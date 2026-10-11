"""Posts normalised events to the origin API. Ingested items are always
information_type=claim — verification is a separate, audited step."""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import API_URL, api_headers  # noqa: E402

from .items import RawItem


def post_event(item: RawItem, event_type: str, confidence: float) -> dict:
    payload = {
        "title": item.title[:500],
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
    resp = httpx.post(f"{API_URL}/events", json=payload, headers=api_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()
