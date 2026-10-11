"""The machine-corroboration promotion gate — one function, fully tested.

Criteria (docs/AUDIT_CRITERIA.md, incl. HRA self-audit findings):
- recency not stale;
- source eligibility with coverage parity: institutional, OR a human-ratified
  vetted source with >=2 independent corroborating publishers;
- fail-closed: the analyst panel must have actually run, with zero consensus
  objections;
- exposure gate: named actors or exact coordinates require a human;
- only ever from `unverified` — human decisions are untouchable.
"""


def promotable(sig: dict, op: dict | None, ev: dict) -> bool:
    if sig.get("recency") == "stale":
        return False
    tier = sig.get("source_tier")
    corrob = sig.get("corroborating_events", 0)
    eligible = tier == "institutional" or (tier == "vetted_ratified" and corrob >= 2)
    if not eligible or corrob < 1:
        return False
    if not op or not op.get("panelists") or op.get("consensus_count", 0) > 0:
        return False
    if ev.get("actors") or ev.get("location") is not None:
        return False
    return ev.get("verification_status") == "unverified"
