"""Human review / verification layer.

Rules enforced here, not left to convention:
- every decision carries a reviewer identity and a written note;
- the audit trail is append-only (no update/delete endpoints exist);
- `retracted` re-opens only when new evidence was added after the retraction
  (human-led: more data can change any decision, but only through evidence);
- a claim becomes an observed_fact only through a `verified` decision;
- corrections (country, event_type, confidence) are diffed into the audit row.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..models import Event, Evidence, ReviewDecision
from ..schemas import (
    EventType,
    InformationType,
    ReviewDecisionIn,
    ReviewRecordOut,
    VerificationStatus,
)
from .events import _to_out

router = APIRouter(tags=["review"])


def get_reviewer(request: Request) -> str:
    """Reviewer identity. In production this comes from Cloudflare Access
    (the gateway/tunnel is Access-protected, and Access injects the header
    after authenticating the user). X-Reviewer is accepted in development only."""
    email = request.headers.get("cf-access-authenticated-user-email")
    if not email and settings.environment == "development":
        email = request.headers.get("x-reviewer")
    if not email:
        raise HTTPException(401, "reviewer identity required (Cloudflare Access)")
    return email


@router.get("/review/queue")
async def review_queue(
    country: str | None = None,
    event_type: EventType | None = None,
    limit: int = Query(default=50, le=500),
    session: AsyncSession = Depends(get_session),
):
    base = select(Event).where(Event.human_review == False)  # noqa: E712
    if country:
        base = base.where(Event.country == country.upper())
    if event_type:
        base = base.where(Event.event_type == event_type)
    total = (
        await session.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    rows = (
        (await session.execute(base.order_by(Event.date_time.asc()).limit(limit)))
        .scalars()
        .all()
    )
    return {"pending": total, "events": [_to_out(e) for e in rows]}


@router.post("/events/{event_id}/review", response_model=ReviewRecordOut, status_code=201)
async def review_event(
    event_id: str,
    body: ReviewDecisionIn,
    reviewer: str = Depends(get_reviewer),
    session: AsyncSession = Depends(get_session),
):
    ev = await session.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "event not found")
    if ev.verification_status == VerificationStatus.RETRACTED:
        last_retraction = (
            await session.execute(
                select(ReviewDecision.created_at)
                .where(ReviewDecision.event_id == event_id,
                       ReviewDecision.new_status == VerificationStatus.RETRACTED)
                .order_by(ReviewDecision.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        new_evidence = (
            await session.execute(
                select(func.count()).select_from(Evidence)
                .where(Evidence.event_id == event_id,
                       Evidence.created_at > last_retraction)
            )
        ).scalar_one() if last_retraction else 0
        if not new_evidence:
            raise HTTPException(
                409,
                "event is retracted; add new external evidence to re-open the decision",
            )

    changes: dict[str, dict] = {}
    if body.corrections:
        for field in ("country", "event_type", "confidence"):
            new = getattr(body.corrections, field)
            if new is None:
                continue
            if field == "country":
                new = new.upper()
            old = getattr(ev, field)
            if old != new:
                changes[field] = {"from": old, "to": new}
                setattr(ev, field, new)

    previous_status = ev.verification_status
    ev.verification_status = body.status
    ev.human_review = True

    # A claim becomes an observed fact only via an explicit `verified` decision.
    if body.status == VerificationStatus.VERIFIED and ev.information_type == InformationType.CLAIM:
        changes["information_type"] = {
            "from": InformationType.CLAIM,
            "to": InformationType.OBSERVED_FACT,
        }
        ev.information_type = InformationType.OBSERVED_FACT

    record = ReviewDecision(
        event_id=event_id,
        reviewer=reviewer,
        previous_status=previous_status,
        new_status=body.status,
        note=body.note,
        sources_consulted=[str(u) for u in body.sources_consulted],
        changes=changes,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/events/{event_id}/history", response_model=list[ReviewRecordOut])
async def event_history(event_id: str, session: AsyncSession = Depends(get_session)):
    if await session.get(Event, event_id) is None:
        raise HTTPException(404, "event not found")
    rows = (
        (
            await session.execute(
                select(ReviewDecision)
                .where(ReviewDecision.event_id == event_id)
                .order_by(ReviewDecision.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    return rows
