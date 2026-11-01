# Prioritization Policy — how anything gets ordered here

Every ordering the platform produces — what agents emphasize, how events are
sorted, how proposals are ranked — must trace to the published frameworks in
[docs/references/](references/), never to model preference or operator whim.
This file is the policy; `pipelines/norms.py` is its injectable form.

## The anchors

| Anchor | Source | Rule it contributes |
|---|---|---|
| Prevention first | [A New Agenda for Peace](references/un-peace-and-digital-framework.md) (UN SG, 2023) | Earlier, closer to the affected community, de-escalating > later, remote, reactive |
| Information integrity | [Global Digital Compact](references/un-peace-and-digital-framework.md) (A/RES/79/1, Annex I) | Independent, fact-based, timely information; blackouts are risk signals, not absence of risk |
| Civilian impact first | [DPG Standard, indicator 9](references/dpg-alliance.md) (do no harm by design) | Population impact and health strain outweigh strategic/economic/reputational considerations |
| Machines propose, humans dispose | [APDSI letter, Art. 86-C spirit](references/apdsi-un-charter-reform.md) | Every machine ordering is advisory input to a human decision; never a final ranking of countries or peoples |

## Where each ordering implements them

| Surface | Mechanism | Anchor applied |
|---|---|---|
| Analyst desks (`pipelines/audit/desks.py`) | `NORMATIVE_ANCHORS` injected into every panelist's system prompt | Which concerns to surface first; blackout-as-signal |
| Solutions agents (`pipelines/solutions/engine.py`) | `NORMATIVE_ANCHORS` appended to both lens prompts | Prevention-first option drafting; civilian impact first |
| HRA prioritized actions (`pipelines/hra/vitals.py: immune_response`) | Deterministic sort by vital score; alarm→urgent→human dispatch | Civilian impact first (vitals are per-country absolute conditions — never a league table) |
| Public feed | Date descending, published statuses only | Information integrity (timeliness; verified only) |
| Peace Proposals (`frontend/src/Proposals.tsx`) | Transparent composite: 0.35 population + 0.25 health + 0.25 armed-violence + 0.15 poverty, components shown | Civilian impact first (population + health = 0.60 of the weight); formula public by design |

## Rules for changing a weight or ordering

1. Any change must name the anchor that justifies it, in the commit message
   and in the code comment at the weight.
2. No surface may introduce a country ranking framed as merit or blame —
   orderings express *situation pressure and response priority* only.
3. Machine orderings remain advisory: nothing dispatches, publishes a verdict,
   or escalates without the human path defined in [GOVERNANCE.md](GOVERNANCE.md).
