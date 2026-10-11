"""Public feed — the only event surface meant for unauthenticated visitors.

Governance (docs/GOVERNANCE.md): the public layer shows exclusively events a
human reviewer has confirmed (verified or partially_verified). Claims under
review, disputed and retracted events never appear here.
"""
import hashlib
import re
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from neo4j import AsyncGraphDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..models import Contribution, Event
from ..schemas import ContributionIn, ContributionOut, EventOut, VerificationStatus
from .events import _to_out

router = APIRouter(prefix="/public", tags=["public"])

PUBLIC_STATUSES = (VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_VERIFIED)


@router.get("/events", response_model=list[EventOut])
async def public_events(
    limit: int = Query(default=500, le=2000),
    session: AsyncSession = Depends(get_session),
):
    q = (
        select(Event)
        .where(Event.verification_status.in_(PUBLIC_STATUSES))
        .order_by(Event.date_time.desc())
        .limit(limit)
    )
    rows = (await session.execute(q)).scalars().all()
    return [_to_out(e) for e in rows]


@router.get("/arms-transfers")
async def arms_transfers(
    country: str | None = Query(default=None, description="ISO2 or country name"),
    limit: int = Query(default=200, le=1000),
):
    """Documented arms transfers from the actor graph (SIPRI Arms Transfers
    Database, loaded via pipelines/sipri). Relationships with evidence and
    attribution — never a ranking. TIV values are SIPRI trend-indicator
    values, not prices."""
    where = ""
    params: dict = {"limit": limit}
    if country:
        where = ("WHERE s.iso2 = $c OR r.iso2 = $c "
                 "OR toLower(s.name) = toLower($c) OR toLower(r.name) = toLower($c)")
        params["c"] = country.upper() if len(country) == 2 else country
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        async with driver:
            records, _, _ = await driver.execute_query(
                f"""
                MATCH (s:Country)-[t:SUPPLIED]->(r:Country) {where}
                RETURN s.name AS supplier, r.name AS recipient, properties(t) AS transfer
                ORDER BY transfer.delivery_year DESC LIMIT $limit
                """,
                **params,
            )
    except Exception as exc:  # noqa: BLE001 — graph store down must not 500 opaquely
        raise HTTPException(503, f"actor graph unavailable: {type(exc).__name__}")
    return {
        "attribution": "Source: SIPRI Arms Transfers Database (where source=SIPRI); "
                       "TIV values are SIPRI trend-indicator values, not prices.",
        "count": len(records),
        "transfers": [dict(rec["transfer"], supplier=rec["supplier"], recipient=rec["recipient"])
                      for rec in records],
    }


# ---- public contributions: minimal, spam-gated, never auto-incorporated ----

_RATE: dict[str, list[float]] = {}
RATE_MAX, RATE_WINDOW = 5, 3600  # 5 submissions per hour per client

PII_PATTERNS = re.compile(
    r"\b[\w.+-]+@[\w-]+\.[\w.]+\b|\+?\d[\d\s().-]{8,}\d"
)


def _client_key(request: Request) -> str:
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")
    # hashed, in-memory only — never persisted (data minimisation)
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


@router.post("/contributions", response_model=ContributionOut, status_code=202)
async def submit_contribution(
    body: ContributionIn, request: Request, session: AsyncSession = Depends(get_session)
):
    """Public submissions enter the moderation pipeline as claims
    (docs/GOVERNANCE.md). Honeypot, rate limit, size caps, PII screen."""
    now = time.monotonic()
    key = _client_key(request)
    window = [t for t in _RATE.get(key, []) if now - t < RATE_WINDOW]
    if len(window) >= RATE_MAX:
        raise HTTPException(429, "rate limit: try again later")
    _RATE[key] = window + [now]

    text = body.text.strip()
    if PII_PATTERNS.search(text):
        raise HTTPException(
            422,
            "please remove personal data (emails, phone numbers) — testimonies are pseudonymised by design",
        )
    if body.event_id and await session.get(Event, body.event_id) is None:
        raise HTTPException(404, "referenced event not found")

    record = Contribution(event_id=body.event_id, text=text,
                          url=str(body.url) if body.url else None)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record
