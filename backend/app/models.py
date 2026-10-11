import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import JSON, Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .schemas import EventType, InformationType, VerificationStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    actors: Mapped[list] = mapped_column(JSON, default=list)
    event_type: Mapped[EventType] = mapped_column(String, index=True)
    information_type: Mapped[InformationType] = mapped_column(
        String, default=InformationType.CLAIM
    )
    source_urls: Mapped[list] = mapped_column(JSON, default=list)
    source_language: Mapped[str] = mapped_column(String(8), default="en")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String, default=VerificationStatus.UNVERIFIED, index=True
    )
    civilian_impact: Mapped[dict] = mapped_column(JSON, default=dict)
    human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_audit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class ReviewDecision(Base):
    """Append-only audit trail. No update or delete path exists in the API;
    production should also revoke UPDATE/DELETE on this table at the DB level."""

    __tablename__ = "review_decisions"

    review_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(String, index=True)
    reviewer: Mapped[str] = mapped_column(String)
    previous_status: Mapped[VerificationStatus] = mapped_column(String)
    new_status: Mapped[VerificationStatus] = mapped_column(String)
    note: Mapped[str] = mapped_column(String)
    sources_consulted: Mapped[list] = mapped_column(JSON, default=list)
    changes: Mapped[dict] = mapped_column(JSON, default=dict)  # field → {from, to}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Evidence(Base):
    """Append-only external evidence attached to an event. Validated against
    outside sources at submission (reachability, source tier, cross-check
    coverage); the verdict it enables remains a human decision."""

    __tablename__ = "evidence"

    evidence_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str] = mapped_column(String, index=True)
    submitted_by: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String(1000))
    direction: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String)
    source_tier: Mapped[str] = mapped_column(String, default="unknown")
    reachable: Mapped[bool] = mapped_column(Boolean, default=False)
    covers_cross_check: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Contribution(Base):
    """Public contribution awaiting moderation (docs/GOVERNANCE.md workflow:
    contribution -> spam/PII screen -> classification -> verification ->
    moderator review). Stored as a claim; incorporation is a human act
    (typically: a reviewer attaches it as evidence)."""

    __tablename__ = "contributions"

    contribution_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    text: Mapped[str] = mapped_column(String(2000))
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String, default="received", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HRAPosition(Base):
    """Append-only published positions of the Human Rights Agent."""

    __tablename__ = "hra_positions"

    position_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    statement: Mapped[str] = mapped_column(String(4000))
    vitals: Mapped[dict] = mapped_column(JSON, default=dict)
    priorities: Mapped[list] = mapped_column(JSON, default=list)
    platform_audit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    engine: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
