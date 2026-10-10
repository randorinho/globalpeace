"""ReliefWeb reports API connector.

API v2 requires a REGISTERED appname (v1 is decommissioned; unregistered
appnames get 403): https://apidoc.reliefweb.int/parameters#appname
Until one is approved, use the ReliefWeb country RSS feeds (kind: rss).
"""
import os
from datetime import datetime

import httpx

from ..items import RawItem
from ..registry import SourceConfig

API = "https://api.reliefweb.int/v2/reports"
APPNAME = os.environ.get("RELIEFWEB_APPNAME", "")


def fetch_reliefweb(cfg: SourceConfig) -> list[RawItem]:
    if not APPNAME:
        raise RuntimeError("set RELIEFWEB_APPNAME (registered appname) to use the ReliefWeb API")
    body = {
        "filter": {"field": "country.iso3", "value": cfg.rw_country},
        "limit": cfg.limit,
        "sort": ["date.created:desc"],
        "fields": {"include": ["title", "url", "date.created", "language.code", "source.name"]},
    }
    resp = httpx.post(API, params={"appname": APPNAME}, json=body, timeout=30)
    resp.raise_for_status()
    items: list[RawItem] = []
    for row in resp.json().get("data", []):
        f = row.get("fields", {})
        if not f.get("url") or not f.get("date", {}).get("created"):
            continue
        langs = f.get("language") or [{"code": "en"}]
        items.append(
            RawItem(
                source_id=cfg.id,
                title=f.get("title", ""),
                url=f["url"],
                published=datetime.fromisoformat(f["date"]["created"]),
                language=langs[0].get("code", "en"),
                country=cfg.country,
                extra={"publisher": [s.get("name") for s in f.get("source", [])]},
            )
        )
    return items
