# Human Review Security Policy — DRAFT (not yet deployed)

**Status: DRAFT.** Until this policy is adopted and its controls deployed,
human review access stays limited to the platform operator through the
secret-gated local dashboard. Expanding reviewer access without these
controls is prohibited — an open review surface is the platform's single
largest manipulation vector.

## Purpose

Prevent unsecured behaviour and political manipulation of the verification
layer. Whoever controls "verified" controls the public map; this policy makes
that power auditable, distributed, and revocable.

## Threat model

| Threat | Vector |
|---|---|
| Reviewer impersonation | Spoofed identity headers; stolen credentials |
| Insider bias | A legitimate reviewer verifying/retracting along political lines |
| Coordinated capture | A group of reviewers aligned to one actor steering statuses |
| Evidence laundering | Sock-puppet "external evidence" used to re-open or flip decisions |
| Pressure on reviewers | Identified reviewers coerced over specific events |

## Controls required before any reviewer expansion

1. **Identity**: Cloudflare Access in front of all review APIs; MFA mandatory;
   reviewer identity taken exclusively from the Access-authenticated email —
   header-asserted identity is disabled the day Access is live.
2. **Vetted roster**: reviewers are named, vetted individuals with declared
   conflicts of interest, affiliated organisations on record, and signed
   acceptance of this policy. No anonymous reviewers.
3. **Diversity rule**: for any country, the reviewer pool must not be
   majority-affiliated with any single state, party, or organisation.
4. **Two-person rule**: `verified` and `retracted` on events with
   civilian-impact figures require two independent reviewers; the second
   reviewer must not share an affiliation with the first.
5. **Self-dealing ban**: a reviewer may not decide on events where they
   submitted the evidence or the contribution being weighed.
6. **Append-only everything** (deployed): decisions, evidence, and machine
   promotions share one immutable trail; deletion is impossible by design.
7. **Anomaly monitoring**: alerts on volume spikes per reviewer, systematic
   one-direction decisions per country, and off-hours bursts; monthly audit
   of a random decision sample against the written criteria.
8. **Revocation**: any roster member can be suspended immediately by the
   operator; all their undisputed decisions within the review window are
   flagged for re-review.
9. **Pressure protection**: reviewers may be pseudonymous publicly (identity
   held by the platform), per GOVERNANCE.md — never anonymous internally.

## Interim regime (now, while this policy is DRAFT)

- Publication proceeds through **machine corroboration**: `ai_corroborated`
  status, granted only when an institutional source, independent
  corroboration, and recency hold and the analyst panel raised no consensus
  objection. It is publicly labeled as machine-corroborated, never presented
  as human verification, and **never overrides any human decision**.
- The local operator dashboard remains fully functional (gateway-secret
  gated, not internet-exposed) and displays each AI agent's process per event.
- Every machine promotion is recorded in the append-only decision trail,
  attributed to `ai-pipeline(continental-desks)`, with the platform operator
  as the accountable human for the pipeline's conduct.

## Sunset of the interim regime (decision on HRA finding #2)

The machine-corroboration regime is **transitional by design**: it ends
automatically when this policy's activation checklist completes. From that
point, `ai_corroborated` becomes a queueing label only — publication tiers
revert to human decisions. The Human Rights Agent continues to publish the
compliance tension until then; that persistent public record is intentional.

## Activation checklist

- [ ] Controls 1–9 deployed and tested
- [ ] Policy adopted (operator sign-off recorded in the repo history)
- [ ] Reviewer roster seeded per the diversity rule
- [ ] Edge allowlist opened for `/api/review/*` behind Access
- [ ] Header-asserted reviewer identity disabled in `review.py`
