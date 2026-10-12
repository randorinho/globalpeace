# Contributing to globalpeace.ai

Thank you for considering a contribution to the peace commons. This project
is AGPL-3.0 and governed by the documents in `docs/` — read
[GOVERNANCE.md](docs/GOVERNANCE.md) and [AUDIT_CRITERIA.md](docs/AUDIT_CRITERIA.md)
before proposing changes to anything that touches verification, publication,
or trust.

## Developer Certificate of Origin (DCO)

All contributions require a DCO sign-off. By signing off, you certify the
[Developer Certificate of Origin 1.1](https://developercertificate.org/) —
in short: you wrote the contribution or otherwise have the right to submit
it under this project's open-source license.

Sign off every commit:

```bash
git commit -s -m "Your change"
```

This appends `Signed-off-by: Your Name <your@email>` to the commit message.
The name must be your real name or an established identity — anonymous
sign-offs cannot certify origin. Pull requests with unsigned commits will
not be merged (`git rebase --signoff` fixes a branch retroactively).

## Workflow

1. Fork, branch from `dev` (never `main` — `main` mirrors production).
2. Make the change; match the surrounding code's style and idiom.
3. Run the checks CI will run:
   - `python -m pytest tests/` (governance invariants are the crown jewels)
   - `cd frontend && npm run build`
   - `cd edge/gateway && npx tsc --noEmit`
4. Open a PR against `dev` with a clear description of what and why.
5. CI must be green; a maintainer reviews and merges. Promotions to `main`
   happen only through the guarded deploy ritual.

## Hard lines (will not be merged)

- Anything enabling machines to verify events or dispatch external
  communications autonomously — human accountability is constitutional here.
- Weakening the exposure gate, PII screens, append-only trails, or the
  fail-closed promotion logic.
- Country rankings, moral-geography visualizations, or publication of
  named individuals / sub-national armed-actor links (see
  [DATA_MODEL.md](docs/DATA_MODEL.md)).
- Secrets, credentials, or personal data in the repository — in any commit.

## Scope guidance

Good first contributions: source connectors for pilot regions (with the
vetting workflow), translations, geolocation precision, test coverage,
accessibility. Open an issue first for anything architectural — the
[backlog](docs/BACKLOG.md) shows where help lands best.

## Conduct

Be the kind of contributor a peace platform deserves: factual, respectful,
and patient with disagreement. Harassment or dehumanising language —
toward anyone, including people in the regions we cover — ends the
collaboration.
