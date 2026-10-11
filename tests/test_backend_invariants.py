"""Governance invariants encoded in the backend schemas (no DB needed)."""
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.schemas import (  # noqa: E402
    AuditIn, ContributionIn, EventCreate, InformationType, VerificationStatus,
)


def test_ingested_events_default_to_unverified_claim():
    ev = EventCreate(date_time="2026-10-10T00:00:00Z", country="SD", event_type="attack")
    assert ev.information_type == InformationType.CLAIM
    assert ev.confidence == 0.0


def test_ai_corroborated_is_a_distinct_labeled_status():
    assert VerificationStatus.AI_CORROBORATED.value == "ai_corroborated"
    assert VerificationStatus.AI_CORROBORATED != VerificationStatus.VERIFIED


def test_contribution_honeypot_must_stay_empty():
    with pytest.raises(ValidationError):
        ContributionIn(text="legitimate looking text here", website="http://spam")
    ok = ContributionIn(text="legitimate looking text here", website="")
    assert ok.website == ""


def test_contribution_size_caps():
    with pytest.raises(ValidationError):
        ContributionIn(text="short", website="")  # < 10 chars
    with pytest.raises(ValidationError):
        ContributionIn(text="x" * 2001, website="")


def test_audit_requires_bounded_score_and_known_verdict():
    with pytest.raises(ValidationError):
        AuditIn(verdict="definitely_true", score=0.5, engine="rules-v1")
    with pytest.raises(ValidationError):
        AuditIn(verdict="credible_recent", score=1.5, engine="rules-v1")
