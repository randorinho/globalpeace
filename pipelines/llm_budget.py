"""Central LLM guardrails — one model, one kill switch, one daily budget.

Added after the 1–3 Nov cost runaway (~$187 in two days: six desks × six
Opus panelists every 30 minutes, plus full solutions redrafts each cycle,
around the clock). Every agent call now goes through here:

- GPAI_LLM_DISABLED=1        kill switch — no agent calls, rules-only
- GPAI_LLM_MODEL             default claude-sonnet-5 (was hardcoded Opus)
- GPAI_LLM_DAILY_CALL_CAP    default 400 calls per UTC day, persisted state

Callers check allowed(n) before a batch and record spend(n) per call; when
the cap is hit the pipeline degrades to the transparent rules engine —
loudly, never silently. throttle()/unchanged() stop redundant re-work
(HRA self-audit interval; solutions redrafts only when a situation's
event set actually changed).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE = Path(__file__).parent / ".state" / "llm_budget.json"
MODEL = os.environ.get("GPAI_LLM_MODEL", "claude-sonnet-5")
DAILY_CAP = int(os.environ.get("GPAI_LLM_DAILY_CALL_CAP", "400"))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load() -> dict:
    try:
        d = json.loads(STATE.read_text())
    except Exception:  # noqa: BLE001 — missing/corrupt state resets safely
        d = {}
    if d.get("date") != _today():
        d = {"date": _today(), "calls": 0, "fp": d.get("fp", {}), "ts": d.get("ts", {})}
    d.setdefault("fp", {})
    d.setdefault("ts", {})
    return d


def _save(d: dict) -> None:
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(d))


def disabled() -> bool:
    return os.environ.get("GPAI_LLM_DISABLED", "") not in ("", "0")


def allowed(n: int = 1) -> bool:
    """May the caller make n agent calls right now? Loud when not."""
    if disabled():
        print("llm_budget: GPAI_LLM_DISABLED set — rules-only", file=sys.stderr)
        return False
    d = _load()
    if d["calls"] + n > DAILY_CAP:
        print(f"llm_budget: daily cap {DAILY_CAP} reached ({d['calls']} used) — "
              "rules-only until UTC midnight", file=sys.stderr)
        return False
    return True


def spend(n: int = 1) -> None:
    d = _load()
    d["calls"] += n
    _save(d)


def throttle(key: str, hours: float) -> bool:
    """True if `key` may run now (last run older than `hours`); records the run."""
    d = _load()
    now = datetime.now(timezone.utc)
    last = d["ts"].get(key)
    if last:
        try:
            age_h = (now - datetime.fromisoformat(last)).total_seconds() / 3600
            if age_h < hours:
                print(f"llm_budget: {key} throttled ({age_h:.1f}h < {hours}h)", file=sys.stderr)
                return False
        except ValueError:
            pass
    d["ts"][key] = now.isoformat()
    _save(d)
    return True


def unchanged(key: str, fingerprint: str) -> bool:
    """True if `fingerprint` matches the stored one for `key` — the work can
    be skipped. Read-only: call record() only after the work SUCCEEDS, so a
    failed attempt is retried next cycle instead of skipped forever."""
    return _load()["fp"].get(key) == fingerprint


def record(key: str, fingerprint: str) -> None:
    d = _load()
    d["fp"][key] = fingerprint
    _save(d)
