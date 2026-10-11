# AI Audit Criteria

The AI audit is a **triage stage between ingestion and human review**. It never
verifies: its only outputs are a recommendation, named doubts, and the list of
cross-checks a human reviewer must perform. `human_review_required` is always
true. The goal is to surface late (recent) and credible intelligence first, and
to make every doubt explicit.

## Core distinctions (why "cited by a credible source" is not "verified")

1. **Publication authenticity** — is this really a FEWS NET / UNHCR / OCHA
   publication? (checkable from the source domain and feed)
2. **Substantive credibility** — is the originating source analytically
   credible for this topic?
3. **Independent corroboration** — have the *underlying figures* been checked
   against their primary datasets? A FEWS NET report citing ACLED conflict
   counts does not verify those counts; only ACLED's dataset does. Figures and
   methodology-defined terms ("affected N people") must be interpreted per the
   originating dataset's methodology.

An event can score high on 1 and 2 and still be `needs_additional_verification`
because 3 is incomplete. That is the normal case, not a failure.

## Transparent rules (pipelines/audit/criteria.py)

| Signal | Rule |
|---|---|
| Recency ("late intelligence") | < 3 days = fresh · 3–14 days = recent · > 14 days = stale |
| Source tier | institutional domain (reliefweb.int, *.un.org, unhcr.org, fews.net, acleddata.com…) > known NGO > unknown > no source |
| Corroboration | other ingested events, same country, ±7 days, from a *different* source domain |
| Specificity | has title, has source URL, has location, has actors |
| Cross-check matrix | displacement/refugee figures → UNHCR · conflict-event counts → ACLED dataset · price/market figures → FEWS NET market data + local monitoring · "affected N people" → interpret per ACLED methodology |

## Verdicts

- `credible_recent` — institutional source, fresh/recent, corroborated,
  no unresolved doubt. Still requires human review before any status change.
- `needs_additional_verification` — **any** doubt under the criteria above:
  single-source, uncorroborated figures, methodology-sensitive claims,
  unknown source tier. The audit lists exactly which cross-checks are needed.
- `stale_low_priority` — older than the recency window; deprioritised, not dropped.

## Operational classification

A high-credibility early-warning signal is classified for **monitoring and
human review** — never for automatic diplomatic action (docs/ARCHITECTURE.md
recommendation levels: informational → preventive → urgent, with the urgent
path always human-routed).

## Optional LLM analyst (pipelines/audit/llm.py)

A Claude analyst can add a second opinion (concerns the rules missed, summary
for the reviewer). It is advisory: it cannot change the rules verdict upward,
only flag additional doubt. Runs only when API credentials are configured.

## Continental analyst desks (pipelines/audit/continents.py, desks.py)

The LLM layer is organised as **six continental desks** — Africa, Asia,
Europe, North America, South America, Oceania — each deploying a panel of
**six analyst agents** over its region's current reporting digest. Each
panelist analyses the same digest under a distinct lens: source criticism,
methodology, regional context, corroboration independence, temporal
consistency, humanitarian impact.

Aggregation (same-direction opinions): every concern is attributed to its
lens; concerns raised independently by two or more panelists are counted as
panel consensus. Panels are advisory — any concern can downgrade
`credible_recent` to `needs_additional_verification`, and nothing a panel
says can upgrade a verdict or mark anything verified. Desks run only where
there are unaudited events, and the pipeline degrades to rules-only when the
LLM layer is unavailable.

Run: `python -m audit.run --with-desks` (panel size configurable via
`--panel-size`; requires Anthropic API credentials on the pipeline host).
