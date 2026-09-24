# Contributing — One-Command Hospital

Thanks for helping build the boring-but-vital layer between hospital
guidelines and AI. This project has one rule that outranks all others:

> **A wrong confident answer is worse than an honest refusal.**
> Every contribution must preserve that ordering.

## Ground rules

1. **No real PHI, ever.** Test fixtures use obviously synthetic identifiers
   (Synthea patients, "Robert Smith" with a fake MRN). If your change
   touches text handling, assume a reviewer will grep your diff for
   narrative-looking strings.
2. **The eval gate is law.** CI runs the 52-question seed set and the
   208-question full set; retrieval must stay ≥80% or the build fails.
   If your change regresses retrieval, fix it or bring evidence + steward
   discussion for why the expected answers changed (corpus edits follow the
   change-control classes in `docs/governance.md`).
3. **Tests are part of the definition of done.** Bug fixes need a regression
   test on the tier where the bug lived (see `tests/README.md` for the tiers
   and the bugs they've already caught).
4. **Honest degradation > silent fallback.** If a component is down or a
   model can't load, the system must SAY SO (metrics, `/health`, flags) —
   never pretend. Code that silently swallows a safety-relevant failure
   will be rejected.

## Local workflow

```bash
make doctor            # preflight
make test-unit         # ~2s, no docker — run this before every push
make test-node
make eval              # seed eval gate
make eval-full         # full 208-question gate
make test-integration  # needs docker; golden path / fail-closed / PHI leak
```

CI (`.github/workflows/ci.yml`) runs: eval gates, python compile + YAML
validity, node syntax + tests + SMART widget build, compose validation +
gitleaks, and the docker integration job.

## Commits & pull requests

- Small, single-purpose PRs. Title: `area: summary` (e.g. `rag: fix margin
  gate off-by-one`).
- CI green is necessary but not sufficient — describe **how you verified**
  the clinical-safety behavior (which tier, which scenario).
- Any change to refusal behavior, de-ID logic, audit format or the FHIR
  payload shape is a **Class B change** under `docs/governance.md`: it needs
  a stated migration/compat note and two reviewers.
- Sign off your commits (`git commit -s`) — DCO.

## Where to start

`docs/deployment_readiness.md` lists the open gaps between the current
research build and a clinical pilot, ordered by gate. `tests/README.md`
lists what the suite proves today. The gap between those two documents IS
the roadmap.
