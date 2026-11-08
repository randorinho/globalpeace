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
    # slow-onset harm gets its own type — and acute types still win over it
    assert classify("Hunger deepens for millions amid conflict") == "humanitarian_crisis"
    assert classify("Ebola outbreak spreads to eighth province") == "humanitarian_crisis"
    assert classify("Inflation and unemployment drive economic hardship") == "humanitarian_crisis"
    assert classify("Famine-stricken town hit by airstrike") == "attack"
    # French reporting (ReliefWeb TD/CD coverage) classifies the same way
    assert classify("Des milliers de déplacés après les affrontements") == "displacement"
    assert classify("Aperçu de l'insécurité alimentaire aiguë") == "humanitarian_crisis"
    assert classify("Attaque contre un convoi humanitaire, douze tués") == "attack"
    assert classify("Cessez-le-feu annoncé après des pourparlers") == "negotiation"


def test_country_matching_global_registry():
    assert match_country("Fighting intensifies in Sudan") == "SD"
    assert match_country("Elections in Belgium") == "BE"
    # longest alias wins: South Sudan is not Sudan, Guinea-Bissau is not Guinea
    assert match_country("Aid convoy reaches South Sudan") == "SS"
    assert match_country("Coup attempt in Guinea-Bissau") == "GW"
    assert match_country("Cholera outbreak in Guinea") == "GN"
    # word boundaries: Niger is not Nigeria, India is not Indiana
    assert match_country("Floods across Nigeria") == "NG"
    assert match_country("Junta consolidates power in Niger") == "NE"
    assert match_country("Indiana state fair opens") is None
    # ambiguous bare names stay unmatched, never guessed
    assert match_country("tensions rise on the Korean peninsula") is None
    assert match_country("No geography here at all") is None


def test_country_registry_is_complete_and_desked():
    from audit.continents import COUNTRY_DESK  # noqa: E402
    from ingest.countries import ALL_ISO2, ISO2_FROM_ISO3  # noqa: E402

    # every registered country has a continental desk — nothing lands unassigned
    undesked = sorted(ALL_ISO2 - COUNTRY_DESK.keys())
    assert not undesked, f"countries without a desk: {undesked}"
    # ReliefWeb attribution path: iso3 -> iso2 covers the whole registry
    assert len(ISO2_FROM_ISO3) == len(ALL_ISO2)
    assert ISO2_FROM_ISO3["COD"] == "CD" and ISO2_FROM_ISO3["SSD"] == "SS"


def test_vitals_cover_health_and_poverty_dimensions():
    from hra.vitals import PLAYBOOK, VITALS, _vitals_for
    assert "health_system" in VITALS and "poverty_and_livelihoods" in VITALS
    assert set(VITALS) == set(PLAYBOOK)  # every vital has a preventive playbook entry
    assert "health_system" in _vitals_for({"title": "Cholera outbreak strains clinics", "event_type": "protest"})
    assert "poverty_and_livelihoods" in _vitals_for({"title": "Inflation deepens poverty as wages collapse", "event_type": "protest"})


def test_normative_anchors_reach_every_prioritizing_prompt():
    from audit.desks import SYSTEM_BASE
    from norms import NORMATIVE_ANCHORS
    from solutions.engine import COMMON_RULES
    assert NORMATIVE_ANCHORS in SYSTEM_BASE
    assert NORMATIVE_ANCHORS in COMMON_RULES
    for anchor in ("PREVENTION FIRST", "INFORMATION INTEGRITY",
                   "CIVILIAN IMPACT FIRST", "MACHINES PROPOSE, HUMANS DISPOSE"):
        assert anchor in NORMATIVE_ANCHORS


def test_ucdp_row_maps_structurally():
    from ingest.connectors.ucdp import _to_item
    from ingest.registry import SourceConfig
    cfg = SourceConfig(id="ucdp-ged", kind="ucdp", confidence=0.8)
    row = {
        "id": 580077, "relid": "MLI-2025-1-15108-152", "type_of_violence": 1,
        "side_a": "Government of Mali", "side_b": "JNIM", "best": 5,
        "where_coordinates": "Dioura town", "adm_1": "Mopti region",
        "where_prec": 1, "latitude": 15.0, "longitude": -4.6,
        "country": "Mali", "date_start": "2025-12-03", "date_end": "2025-12-03",
        "where_description": "Dioura military camp",
    }
    item = _to_item(cfg, "26.1", row)
    assert item.country == "ML" and item.event_type == "attack"  # structured, no regex guessing
    assert item.location == (15.0, -4.6)
    assert item.url == "https://ucdpapi.pcr.uu.se/api/gedevents/26.1?id=580077"
    assert "Government of Mali" in item.title and "5 killed" in item.title
    # GED's historical country labels still resolve via alias matching
    assert _to_item(cfg, "26.1", {**row, "country": "Russia (Soviet Union)"}).country == "RU"
    assert _to_item(cfg, "26.1", {**row, "country": "Myanmar (Burma)"}).country == "MM"
    assert _to_item(cfg, "26.1", {**row, "country": "DR Congo (Zaire)"}).country == "CD"
    # admin/country centroids (where_prec >= 3) are false precision — dropped
    assert _to_item(cfg, "26.1", {**row, "where_prec": 3}).location is None


def test_geolocate_city_scoped_to_country(tmp_path, monkeypatch):
    import ingest.geolocate as g
    def row(name, lat, lon, cc, pop):
        f = ["1", name, name, "", lat, lon, "P", "PPL", cc, "", "", "", "", "", pop, "", "", "", ""]
        return "\t".join(f)
    fx = tmp_path / "cities.txt"
    fx.write_text("\n".join([
        row("El Fasher", "13.62", "25.35", "SD", "252000"),
        row("Nyala", "12.04", "24.88", "SD", "565000"),
        row("Santa Cruz", "-17.78", "-63.18", "BO", "1364000"),
    ]), encoding="utf-8")
    monkeypatch.setattr(g, "GAZETTEER", fx)
    monkeypatch.setattr(g, "_INDEX", None)
    assert g.locate("Fighting near El Fasher displaces thousands", "SD") == (13.62, 25.35)
    assert g.locate("Aid reaches Nyala after weeks of siege", "SD") == (12.04, 24.88)
    # a city name from another country never matches — scoping beats popularity
    assert g.locate("Rally held in Santa Cruz", "SD") is None
    assert g.locate("No city named in this title", "SD") is None


def test_llm_budget_guardrails(tmp_path, monkeypatch):
    import llm_budget as b
    monkeypatch.setattr(b, "STATE", tmp_path / "llm_budget.json")
    monkeypatch.setattr(b, "DAILY_CAP", 3)
    assert b.allowed(3)
    b.spend(3)
    assert not b.allowed(1)          # cap is a hard ceiling
    monkeypatch.setenv("GPAI_LLM_DISABLED", "1")
    assert not b.allowed(0)          # kill switch beats everything
    monkeypatch.delenv("GPAI_LLM_DISABLED")
    # fingerprints: read-only check, explicit record on success
    assert not b.unchanged("solutions:SD", "a,b")
    b.record("solutions:SD", "a,b")
    assert b.unchanged("solutions:SD", "a,b")
    assert not b.unchanged("solutions:SD", "a,b,c")
    # throttle: first call runs, immediate second call is held
    assert b.throttle("hra_statement", 1.0)
    assert not b.throttle("hra_statement", 1.0)


def test_source_tiers():
    assert source_tier(["https://reliefweb.int/report/x"])[0] == "institutional"
    assert source_tier(["https://iom.int/news/x"])[0] == "institutional"
    assert source_tier([])[0] == "none"
    # vetted via registry — test against a controlled registry, not live data
    import audit.criteria as crit
    saved = crit._REGISTRY
    crit._REGISTRY = {
        "provisional.example": {"tier": "vetted", "status": "provisional"},
        "ratified.example": {"tier": "vetted", "status": "ratified"},
        "bad.example": {"tier": "rejected", "status": "ratified"},
    }
    try:
        assert source_tier(["https://provisional.example/a"]) == ("vetted_provisional", 0.6)
        assert source_tier(["https://ratified.example/a"]) == ("vetted_ratified", 0.7)
        assert source_tier(["https://bad.example/a"]) == ("rejected_source", 0.05)
    finally:
        crit._REGISTRY = saved


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


def test_cross_checks_carry_coverage_parity_fallback():
    checks = required_cross_checks("refugees flee across the border")
    assert "regional-organisation monitoring" in checks["refugee_figures"]


def test_promotion_gate_invariants():
    from audit.promotion import promotable
    base_sig = {"source_tier": "institutional", "recency": "fresh", "corroborating_events": 2}
    panel = {"panelists": 6, "consensus_count": 0}
    clean = {"verification_status": "unverified", "actors": [], "location": None}
    assert promotable(base_sig, panel, clean)
    # fail-closed: no panel -> no promotion
    assert not promotable(base_sig, None, clean)
    assert not promotable(base_sig, {"panelists": 0}, clean)
    # exposure gate: actors or exact/unstated-precision location -> human required
    assert not promotable(base_sig, panel, {**clean, "actors": ["Commander X"]})
    assert not promotable(base_sig, panel, {**clean, "location": {"lat": 1, "lon": 2}})
    assert not promotable(base_sig, panel, {**clean, "location": {"lat": 1, "lon": 2}, "location_precision": "exact"})
    # coarse city placement from the public gazetteer is machine-publishable
    assert promotable(base_sig, panel, {**clean, "location": {"lat": 1, "lon": 2}, "location_precision": "city"})
    # human decisions untouchable
    assert not promotable(base_sig, panel, {**clean, "verification_status": "retracted"})
    # coverage parity: ratified vetted source eligible only with >=2 publishers
    vetted = {**base_sig, "source_tier": "vetted_ratified"}
    assert promotable(vetted, panel, clean)
    assert not promotable({**vetted, "corroborating_events": 1}, panel, clean)
    assert not promotable({**base_sig, "source_tier": "vetted_provisional"}, panel, clean)
