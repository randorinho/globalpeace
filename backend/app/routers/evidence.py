"""Evidence layer — human-led external information that can change a decision.

- Submission is validated against outside sources at write time: the URL is
  probed for reachability, its domain is tiered, and it is matched against the
  event's pending cross-checks (UNHCR -> refugee_figures, ACLED ->
  conflict_figures, ...).
- Aggregation: >= 2 same-direction items from distinct institutional domains,
  or any covered cross-check, flags the event ready_for_rereview.
- The system never changes a verdict. It re-opens the door: an event whose
  decision was terminal (retracted) can be re-reviewed only when new evidence
  exists — that gate lives in the review router.
"""
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Event, Evidence
from ..schemas import EvidenceIn, EvidenceOut, EvidenceSummary
from .review import get_reviewer

router = APIRouter(tags=["evidence"])

# Primary-dataset domains -> the cross-check they can cover (docs/AUDIT_CRITERIA.md)
CROSS_CHECK_DOMAINS = {
    "unhcr.org": "refugee_figures",
    "data.unhcr.org": "refugee_figures",
    "acleddata.com": "conflict_figures",
    "fews.net": "market_figures",
    "fdw.fews.net": "market_figures",
    "who.int": "health_figures",
    "extranet.who.int": "health_figures",
}
INSTITUTIONAL = (
    "reliefweb.int", "un.org", "unhcr.org", "wfp.org", "who.int", "unocha.org",
    "fews.net", "acleddata.com", "icrc.org", "data.humdata.org",
)


def _tier(host: str) -> str:
    if any(host == d or host.endswith("." + d) for d in INSTITUTIONAL):
        return "institutional"
    return "unknown"


def _covers(host: str, pending: list[str]) -> str | None:
    for domain, check in CROSS_CHECK_DOMAINS.items():
        if (host == domain or host.endswith("." + domain)) and check in pending:
            return check
    return None


async def _probe(url: str) -> bool:
    """Outside-source validation: is the cited page actually there?"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            r = await client.head(url, headers={"user-agent": "globalpeace-ai-pilot/0.1"})
            if r.status_code == 405:  # some servers reject HEAD
                r = await client.get(url, headers={"user-agent": "globalpeace-ai-pilot/0.1"})
            return r.status_code < 400
    except httpx.HTTPError:
        return False


def summarize(items: list[Evidence]) -> EvidenceSummary:
    directions = {"supports": 0, "contradicts": 0, "context": 0}
    for e in items:
        directions[e.direction] = directions.get(e.direction, 0) + 1
    domains = {urlparse(e.url).hostname for e in items}
    covered = sorted({e.covers_cross_check for e in items if e.covers_cross_check})
    inst_same_direction = max(
        (len({urlparse(e.url).hostname for e in items
              if e.direction == d and e.source_tier == "institutional" and e.reachable})
         for d in ("supports", "contradicts")),
        default=0,
    )
    return EvidenceSummary(
        supports=directions["supports"],
        contradicts=directions["contradicts"],
        context=directions["context"],
        distinct_domains=len(domains),
        cross_checks_covered=covered,
        ready_for_rereview=bool(covered) or inst_same_direction >= 2,
    )


@router.post("/events/{event_id}/evidence", response_model=EvidenceOut, status_code=201)
async def add_evidence(
    event_id: str,
    body: EvidenceIn,
    reviewer: str = Depends(get_reviewer),
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "event not found")

    url = str(body.url)
    host = urlparse(url).hostname or ""
    pending = list((ev.ai_audit or {}).get("cross_checks", {}).keys())

    record = Evidence(
        event_id=event_id,
        submitted_by=reviewer,
        url=url,
        direction=body.direction,
        note=body.note,
        source_tier=_tier(host),
        reachable=await _probe(url),
        covers_cross_check=_covers(host, pending),
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/events/{event_id}/evidence")
async def list_evidence(event_id: str, session: AsyncSession = Depends(get_session)):
    if await session.get(Event, event_id) is None:
        raise HTTPException(404, "event not found")
    rows = (
        (await session.execute(
            select(Evidence).where(Evidence.event_id == event_id)
            .order_by(Evidence.created_at.asc())
        )).scalars().all()
    )
    return {
        "items": [EvidenceOut.model_validate(r) for r in rows],
        "summary": summarize(rows),
    }
