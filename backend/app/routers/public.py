"""Public feed — the only event surface meant for unauthenticated visitors.

Governance (docs/GOVERNANCE.md): the public layer shows exclusively events a
human reviewer has confirmed (verified or partially_verified). Claims under
review, disputed and retracted events never appear here.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Event
from ..schemas import EventOut, VerificationStatus
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
