"""Transparent-rules classifier (docs/ARCHITECTURE.md: 'Transparent rules').

Maps item text to one of the event types, or None — unmatched items are
SKIPPED, never guessed. Priority order matters: the first matching type wins.
Deliberately simple and auditable; an ML classifier can later propose labels,
but rules like these remain the explainable baseline.
"""
import re

RULES: list[tuple[str, list[str]]] = [
    ("displacement", [
        r"\bdisplac", r"\brefugee", r"\bflee\b", r"\bfled\b", r"\bevacuat", r"\bidp\b",
    ]),
    ("attack", [
        r"\battack", r"\bair ?strike", r"\bshelling\b", r"\bbombing\b", r"\bkilled\b",
        r"\bclashes\b", r"\boffensive\b", r"\bambush", r"\bmassacre\b",
    ]),
    ("negotiation", [
        r"\bnegotiat", r"\bceasefire\b", r"\btruce\b", r"\bpeace (deal|talks|agreement|process)\b",
        r"\bmediat", r"\bdialogue\b",
    ]),
    ("protest", [
        r"\bprotest", r"\bdemonstrat", r"\brally\b", r"\briot", r"\bgeneral strike\b",
    ]),
    # Slow-onset humanitarian harm — checked LAST so acute types win when both
    # appear in one title. Feeds the food/health/poverty vitals (hra/vitals.py).
    ("humanitarian_crisis", [
        r"\bfamine\b", r"\bhunger\b", r"\bfood insecur", r"\bmalnutrition\b", r"\bstarvation\b",
        r"\bepidemic\b", r"\boutbreak\b", r"\bcholera\b", r"\bebola\b", r"\bmeasles\b",
        r"\bpoverty\b", r"\bdestitut", r"\blivelihoods?\b", r"\bunemploy",
        r"\binflation\b", r"\beconomic (crisis|collapse|hardship)\b", r"\billicit econom",
    ]),
]

_COMPILED = [(etype, [re.compile(p, re.I) for p in pats]) for etype, pats in RULES]


def classify(text: str) -> str | None:
    for etype, patterns in _COMPILED:
        if any(p.search(text) for p in patterns):
            return etype
    return None


# Name-based country match for sources with no structured country field —
# now the full ISO-3166 registry (see countries.py); unmatched items are
# still skipped, never guessed.
from .countries import match_country  # noqa: E402, F401
