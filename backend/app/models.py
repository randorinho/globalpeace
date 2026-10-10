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
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
