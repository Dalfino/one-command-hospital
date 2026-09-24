# Deployment Readiness Gate

> Verdict as of this writing: **NOT ready for clinical deployment.**
> This is a research/pilot scaffold with real architecture and real evals, running
> on synthetic data. The gap between "works on my machine" and "safe inside a
> hospital" is measured by the gates below. Nothing ships until every gate in
> this document is green — and the person who signs each gate is named, not "the team".

Read this file before touching the demo kiosk. Update it after every milestone.
`docs/governance.md` defines who signs; this file defines what they are signing.

---

## Gate 0 — Scope & classification (blocking)

| Item | Status | Notes |
|---|---|---|
| Intended use statement written | ✅ done | `docs/model_card.md` — advisory, citation-forced, adult inpatient protocols only |
| Regulatory classification determined | ⬜ open | EU: likely high-risk (Annex III via medical device rules) → obligations enforceable Aug 2026. US: likely CDS with non-device pathway *only if* the clinician can independently review the basis (cite-backed answers help); counsel must confirm. UK: DTAC. |
| Advisory-only UX (no autonomous action) | ✅ done | Every answer lands as FHIR Communication + mandatory human sign-off |
| Kill criteria agreed in writing | ✅ done | `docs/architecture.md` — 85% grounding floor, PHI one-strike, >8s median latency, trust <80% |

## Gate 1 — Accuracy (blocking)

| Item | Status | Current evidence |
|---|---|---|
| Known-answer eval ≥ 80% retrieval | ✅ 95% | 208-question set (`eval/qa_full.yaml`): 146/153 answerable, BM25-only |
| Seed eval ≥ 80% | ✅ 98% | 52-question seed: 41/42 |
| Refusal traps all refused (live mode) | ⬜ open | 55 traps defined (10 seed + 45 generated); refusal behavior requires the live stack + GPU. CI currently scores retrieval only. |
| Full-mode grounding ≥ 85% (live) | ⬜ open | Verifier is ConText + heuristics v0.2 — needs the live harness run and sign-off |
| 3+ real hospital protocols loaded & clinician-audited | ⬜ open | Corpus is 3 SYNTHETIC protocols. Real guideline ingestion is Phase 2, with P&T / Quality committee sign-off per document. |
| Ombudsman-style spot checks (weekly, first 8 weeks) | ⬜ open | Governance committee samples 20 answers/week against source |

## Gate 2 — Security (blocking)

| Item | Status | Notes |
|---|---|---|
| Container hardening baseline | ✅ done | non-root USER, cap_drop ALL, no-new-privileges, read-only rootfs on AI services, internal DB network, body caps, rate limits |
| Secrets from env only, `.env` git-ignored | ✅ done | `.env.example` documents all vars; CI gitleaks scan added |
| Question + context both de-identified before LLM | ✅ done | mediator v0.3 scrubs the question too (was context-only) |
| TLS everywhere (no plaintext HTTP hops) | ⬜ open | Compose sandbox is HTTP inside the Docker network; production must terminate TLS at the bus/reverse proxy and encrypt intra-cluster hops |
| Medplum Bot auth enabled (no unauthenticated writeback) | ⬜ open | Works (`medplum-auth.js`), but sandbox default is still `unauthenticated-v0`; production forbids it |
| Threat model reviewed by hospital IT security | ⬜ open | STRIDE-style pass over the 7-hop lifecycle |
| Independent penetration test | ⬜ open | Third party, including the SMART launch flow |
| Secrets rotation & BAAs in place | ⬜ open | Any credential ever pasted in chat/emails must be rotated; BAAs for any cloud component |

## Gate 3 — Infrastructure (blocking)

| Item | Status | Notes |
|---|---|---|
| Healthchecks + dependency-gated startup | ✅ done | Compose `service_healthy` conditions; `make doctor` preflight |
| Observability profile (metrics + alerts + dashboards) | ✅ done | `make observe`: Prometheus, 7 alert rules, 8-panel Grafana |
| CI gate on every push | ✅ done | `.github/workflows/ci.yml`: eval gates, compiles, YAML, secret scan |
| Structured logs with request IDs, shipped off-box | ⬜ open | Services log plainly; add request-id propagation + log shipping (Loki/OTLP) before pilot |
| Backup/restore tested (DBs + audit log) | ⬜ open | Volumes exist; restore drills not yet run |
| Load test at realistic concurrency | ⬜ open | Single-GPU vLLM throughput needs a baseline; alert thresholds assume it |
| Single-host only | ⬜ accepted risk | Compose is one box; HA/failover is a post-pilot decision |

## Gate 4 — AI governance (blocking)

| Item | Status | Notes |
|---|---|---|
| Tamper-evident audit trail | ✅ done | Hash-chained JSONL (`audit.js`), `/audit/verify`, chain-broken alert |
| Human sign-off loop closed end-to-end | ✅ done | `/signoff` → `human_action` updated on the FHIR Communication |
| Model card + intended use | ✅ done | `docs/model_card.md` |
| Governance charter, roles, incident response | ✅ draft | `docs/governance.md` — needs committee ratification |
| Corpus change control (editions, expiry, approval) | ✅ mechanism | Manifest carries edition/effective/expires; expiry-refusal is a documented Phase-2 check |
| Drift & refusal-fatigue monitoring live in prod | ✅ config | Alerts exist; must be pointed at real paging before pilot |
| Bias / equity spot-check on real usage | ⬜ open | Post-pilot: refusal & escalation rates stratified by ward/language |
| Periodic re-eval on corpus change (CI-enforced) | ✅ done | Eval gates run on every push; corpus PR without green eval cannot merge |

## Gate 5 — Smoothness (advisory, pilot-blocking)

| Item | Status | Notes |
|---|---|---|
| SMART widget builds and launches | ✅ done | Vite build green; OpenEMR/SMART launch registration ⬜ open |
| One-command boot + preflight | ✅ done | `make doctor` + `make up` |
| Escalation path visible to clinician in ≤2 clicks | ⬜ open | Widget has escalate button; in-EHR placement needs usability testing |
| Latency budget: p95 ≤ 8s live | ⬜ open | Prefix caching enabled; needs live measurement |
| Clinician feedback channel wired into roadmap | ⬜ open | Simple form → governance review queue |

---

## Sign-off

Each blocking gate needs one named signature (governance roles in `docs/governance.md`):

- [ ] Gate 0 — Clinical sponsor: ______  Date: ____
- [ ] Gate 1 — Quality/Safety lead: ______  Date: ____
- [ ] Gate 2 — IT security lead: ______  Date: ____
- [ ] Gate 3 — Platform/Infra lead: ______  Date: ____
- [ ] Gate 4 — AI governance chair: ______  Date: ____

**Rule: a red item in a blocking gate stops the pilot. No waivers without a
documented risk acceptance signed by the governance chair and reviewed at every
committee meeting until retired.**
