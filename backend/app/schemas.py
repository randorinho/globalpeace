"""Pydantic schemas implementing the data model in docs/DATA_MODEL.md.

The five-type information taxonomy is explicit: nothing enters the system
without being labelled, and a forecast or claim can never be presented as fact.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class InformationType(str, Enum):
    """The five information types. Every stored item carries exactly one."""

    OBSERVED_FACT = "observed_fact"    # confirmed by a source
    CLAIM = "claim"                    # not yet verified
    INTERPRETATION = "interpretation"  # analysis by researchers or AI
    FORECAST = "forecast"              # probability or future scenario
    RECOMMENDATION = "recommendation"  # possible response, never an automatic command


class EventType(str, Enum):
    PROTEST = "protest"
    ATTACK = "attack"
    NEGOTIATION = "negotiation"
    DISPLACEMENT = "displacement"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    RETRACTED = "retracted"


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class EventBase(BaseModel):
    date_time: datetime
    location: Location | None = None
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    actors: list[str] = []
    event_type: EventType
    information_type: InformationType = InformationType.CLAIM
    source_urls: list[HttpUrl] = []
    source_language: str = "en"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    civilian_impact: dict = {}


class EventCreate(EventBase):
    """Incoming events default to CLAIM / UNVERIFIED — verification is a
    separate, audited step and is never implied at ingestion time."""


class EventOut(EventBase):
    event_id: str
    verification_status: VerificationStatus
    human_review: bool
    last_updated: datetime

    model_config = {"from_attributes": True}
