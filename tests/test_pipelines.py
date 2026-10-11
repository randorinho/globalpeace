"""Pipeline unit tests — parsers and audit criteria (no services needed)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipelines"))

from audit.criteria import (  # noqa: E402
    corroboration, publisher_of, required_cross_checks, source_tier,
)
from ingest.classify import classify, match_country  # noqa: E402
from sipri.loader import parse  # noqa: E402

FIXTURE = Path(__file__).parent.parent / "pipelines/sipri/tests/fixture_trade_register.csv"


def test_sipri_parser_reads_fixture_and_estimate_flags():
    transfers = parse(FIXTURE.read_text())
    assert len(transfers) == 3
    assert transfers[0].supplier == "Testland" and not transfers[0].estimated
    assert transfers[1].estimated  # estimate markers set on row 2


def test_classifier_maps_types_and_never_guesses():
    assert classify("Thousands displaced after flooding") == "displacement"
    assert classify("Ceasefire talks resume") == "negotiation"
    assert classify("Airstrike hits market town") == "attack"
    assert classify("Annual fisheries report") is None  # unmatched -> skipped, never guessed


def test_country_matching_only_pilot():
    pilots = {"sudan": "SD", "chad": "TD"}
    assert match_country("Fighting intensifies in Sudan", pilots) == "SD"
    assert match_country("Elections in Belgium", pilots) is None


def test_source_tiers():
    assert source_tier(["https://reliefweb.int/report/x"])[0] == "institutional"
    assert source_tier(["https://iom.int/news/x"])[0] == "institutional"
    assert source_tier([])[0] == "none"
    # vetted via registry (Radio Dabanga, provisionally vetted by the panel)
    tier, score = source_tier(["https://www.dabangasudan.org/en/all-news/x"])
    assert tier == "vetted" and score == 0.65


def test_cross_check_matrix_names_primary_datasets():
    checks = required_cross_checks("Boat capsizes off coast, dozens of migrant deaths")
    assert "migrant_casualty_figures" in checks and "IOM Missing Migrants" in checks["migrant_casualty_figures"]
    market = required_cross_checks("Severe lean season drives food prices up")
    # circularity guard: a FEWS NET claim must not be checked against FEWS NET alone
    assert "market_figures" in market and "WFP VAM" in market["market_figures"]


def test_corroboration_is_publisher_aware_not_domain_based():
    base = dict(country="TD", source_urls=["https://reliefweb.int/report/a"])
    now = datetime(2026, 10, 10, tzinfo=timezone.utc).isoformat()
    ev1 = {**base, "event_id": "1", "date_time": now, "title": "UNHCR: arrivals update"}
    ev2 = {**base, "event_id": "2", "date_time": now, "title": "WFP Chad Country Brief"}
    ev3 = {**base, "event_id": "3", "date_time": now, "title": "UNHCR: second update"}
    # same clearing-house domain, different publishers -> independent
    assert corroboration(ev1, [ev1, ev2, ev3]) == 1  # WFP only (ev3 is same publisher)
    assert publisher_of(ev2) == "WFP"
