"""Generic RSS/Atom connector. Fetches with httpx (explicit timeout), parses
with feedparser — feedparser's own fetching has no timeout control."""
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx

from ..items import RawItem
from ..registry import SourceConfig

UA = "globalpeace-ai-pilot/0.1"


def fetch_rss(cfg: SourceConfig) -> list[RawItem]:
    resp = httpx.get(cfg.url, headers={"user-agent": UA}, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
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
