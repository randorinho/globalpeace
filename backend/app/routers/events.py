from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Event
from ..schemas import AuditIn, EventCreate, EventOut, EventType, Location

router = APIRouter(prefix="/events", tags=["events"])


def _to_out(ev: Event) -> EventOut:
    loc = None
    if ev.geom is not None:
        p = to_shape(ev.geom)
        loc = Location(lat=p.y, lon=p.x)
    return EventOut(
        event_id=ev.event_id,
        title=ev.title,
        ai_audit=ev.ai_audit,
        date_time=ev.date_time,
        location=loc,
        country=ev.country,
        actors=ev.actors,
        event_type=ev.event_type,
        information_type=ev.information_type,
        source_urls=ev.source_urls,
        source_language=ev.source_language,
        confidence=ev.confidence,
        verification_status=ev.verification_status,
        civilian_impact=ev.civilian_impact,
        human_review=ev.human_review,
        last_updated=ev.last_updated,
    )


@router.post("", response_model=EventOut, status_code=201)
async def create_event(body: EventCreate, session: AsyncSession = Depends(get_session)):
    ev = Event(
        title=body.title,
        date_time=body.date_time,
        country=body.country.upper(),
        actors=body.actors,
        event_type=body.event_type,
        information_type=body.information_type,
        source_urls=[str(u) for u in body.source_urls],
        source_language=body.source_language,
        confidence=body.confidence,
        civilian_impact=body.civilian_impact,
    )
    if body.location:
        ev.geom = from_shape(Point(body.location.lon, body.location.lat), srid=4326)
    session.add(ev)
    await session.commit()
    await session.refresh(ev)
    return _to_out(ev)


@router.get("", response_model=list[EventOut])
async def list_events(
    country: str | None = None,
    event_type: EventType | None = None,
    since: datetime | None = None,
    audited: bool | None = None,
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_session),
):
    q = select(Event).order_by(Event.date_time.desc()).limit(limit)
    if audited is True:
        q = q.where(Event.ai_audit.isnot(None))
    elif audited is False:
        q = q.where(Event.ai_audit.is_(None))
    if country:
        q = q.where(Event.country == country.upper())
    if event_type:
        q = q.where(Event.event_type == event_type)
    if since:
        q = q.where(Event.date_time >= since)
    rows = (await session.execute(q)).scalars().all()
    return [_to_out(e) for e in rows]


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: str, session: AsyncSession = Depends(get_session)):
    ev = await session.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "event not found")
    return _to_out(ev)


@router.post("/{event_id}/audit", response_model=EventOut)
async def audit_event(
    event_id: str, body: AuditIn, session: AsyncSession = Depends(get_session)
):
    """Store an AI audit recommendation. Never touches verification_status or
    human_review — verification is exclusively a human decision (review router)."""
    ev = await session.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "event not found")
    ev.ai_audit = {
        **body.model_dump(mode="json"),
        "human_review_required": True,
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }
    await session.commit()
    await session.refresh(ev)
    return _to_out(ev)
