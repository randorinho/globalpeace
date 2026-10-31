"""Generic RSS/Atom connector. Fetches with httpx (explicit timeout), parses
with feedparser — feedparser's own fetching has no timeout control."""
import sys
from datetime import datetime, timezone
from time import mktime, sleep

import feedparser
import httpx

from ..items import RawItem
from ..registry import SourceConfig

UA = "globalpeace-ai-pilot/0.1"


def _get_feed(url: str) -> bytes:
    """GET until a real 200. ReliefWeb answers HTTP 202 with an EMPTY feed
    skeleton while its cache warms — treating that as success silently
    starves ingestion, so 202 is retried, then surfaced as an error."""
    last_status = None
    for attempt in range(4):
        if attempt:
            sleep(2 * attempt)
        resp = httpx.get(url, headers={"user-agent": UA}, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        last_status = resp.status_code
        if resp.status_code == 200:
            return resp.content
        print(f"  feed not ready (HTTP {last_status}), retrying: {url[:80]}", file=sys.stderr)
    raise RuntimeError(f"feed kept answering HTTP {last_status}: {url}")


def fetch_rss(cfg: SourceConfig) -> list[RawItem]:
    feed = feedparser.parse(_get_feed(cfg.url))
    items: list[RawItem] = []
    for entry in feed.entries[: cfg.limit]:
        ts = entry.get("published_parsed") or entry.get("updated_parsed")
        if not ts or not entry.get("link"):
            continue
        items.append(
            RawItem(
                source_id=cfg.id,
                title=entry.get("title", ""),
                url=entry["link"],
                published=datetime.fromtimestamp(mktime(ts), tz=timezone.utc),
                summary=entry.get("summary", ""),
                country=cfg.country,
            )
        )
    return items
