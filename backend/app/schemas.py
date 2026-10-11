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
    # Source-published headline. Only ever a title that the source itself made
    # public — never a generated summary that could name or expose people.
    title: str = Field(default="", max_length=500)
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
    ai_audit: dict | None = None
    verification_status: VerificationStatus
    human_review: bool
    last_updated: datetime

    model_config = {"from_attributes": True}


# --- human review / verification (docs/GOVERNANCE.md: mandatory human review) ---

class EventCorrections(BaseModel):
    """Fields a reviewer may correct, each recorded in the audit trail."""

    country: str | None = Field(default=None, min_length=2, max_length=2)
    event_type: EventType | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ReviewDecisionIn(BaseModel):
    status: VerificationStatus
    note: str = Field(min_length=5, description="Why — required; decisions are never silent")
    sources_consulted: list[HttpUrl] = []
    corrections: EventCorrections | None = None


class ReviewRecordOut(BaseModel):
    review_id: str
    event_id: str
    reviewer: str
    previous_status: VerificationStatus
    new_status: VerificationStatus
    note: str
    sources_consulted: list[str]
    changes: dict
    created_at: datetime

    model_config = {"from_attributes": True}


# --- AI audit (docs/AUDIT_CRITERIA.md) ---

class AuditVerdict(str, Enum):
    CREDIBLE_RECENT = "credible_recent"
    NEEDS_ADDITIONAL_VERIFICATION = "needs_additional_verification"
    STALE_LOW_PRIORITY = "stale_low_priority"


class AuditIn(BaseModel):
    """An AI audit recommendation. It never changes verification_status —
    human_review_required is structurally always true."""

    verdict: AuditVerdict
    score: float = Field(ge=0.0, le=1.0)
    signals: dict = {}
    reasons: list[str] = []
    cross_checks: dict = Field(
        default_factory=dict,
        description="claim-type -> primary dataset a human must check (e.g. refugee_figures -> UNHCR)",
    )
    llm_opinion: dict | None = None
    engine: str = Field(description="e.g. rules-v1, rules-v1+claude-opus-5")


# --- evidence: human-led external info that can change a decision ---

class EvidenceDirection(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXT = "context"


class EvidenceIn(BaseModel):
    url: HttpUrl
    direction: EvidenceDirection
    note: str = Field(min_length=5, description="What this source shows — required")


class EvidenceOut(BaseModel):
    evidence_id: str
    event_id: str
    submitted_by: str
    url: str
    direction: EvidenceDirection
    note: str
    source_tier: str
    reachable: bool
    covers_cross_check: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceSummary(BaseModel):
    """Aggregation: several independent opinions in the same direction, or a
    covered cross-check, make an event ready for human re-review. The system
    never changes the decision itself."""

    supports: int
    contradicts: int
    context: int
    distinct_domains: int
    cross_checks_covered: list[str]
    ready_for_rereview: bool


# --- public contributions (docs/GOVERNANCE.md: public participation) ---

class ContributionIn(BaseModel):
    """Minimal public submission. Always enters as an unverified claim for
    moderation — never incorporated automatically. No account, no PII asked."""

    text: str = Field(min_length=10, max_length=2000)
    url: HttpUrl | None = None
    event_id: str | None = Field(default=None, max_length=64)
    # Honeypot: humans never see this field; bots fill it. Must stay empty.
    website: str = Field(default="", max_length=0)


class ContributionOut(BaseModel):
    contribution_id: str
    event_id: str | None
    text: str
    url: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
