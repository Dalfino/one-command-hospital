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
| Latency budget: p95 ≤ 8s live | ✅ measured (mock) | Live load test executed — see evidence below. GPU-stack re-run still required for the final live-LLM number |
| Clinician feedback channel wired into roadmap | ⬜ open | Simple form → governance review queue |

### Gate 5 evidence — live integration + load run (2026-09-24, native CPU sandbox)

Environment: no docker, no GPU in this sandbox — the four AI services ran as
bare processes with the identical env the test containers get
(`tools/native_stack.sh up-test` / `up-prod`; mock-LLM extractive mode,
Medplum deliberately unreachable). Evidence files in `eval/evidence/`.

**Integration tier — 10/10 PASS** against the live stack (`pytest tests/integration -m integration`):
golden path (cited + grounded + audit seq + X-Request-ID echo), off-corpus
refusal, honest sign-off 502, audit chain verify, PHI white-out through deid
gate AND the persisted Communication payload, fail-closed under a HUNG
verifier (SIGSTOP → upstream timeout → flagged `pending_review`), audit chain
intact after failures.

Bugs the live run caught and fixed (none were catchable by unit tests):
1. **Mediator↔verifier contract**: mediator sent citation *titles* as verifier
   sources → lexical grounding always failed → golden path could never verify
   grounded. Fix: RAG citations now carry the quoted section text
   (`extract_citations(..., section_text)`), mediator forwards `c.text`.
2. **Hung upstream = hung clinician**: no fetch timeout anywhere in the
   mediator. A frozen verifier (GIL stall, network black hole — more realistic
   than a dead container) blocked requests forever. Fix:
   `AbortSignal.timeout(UPSTREAM_TIMEOUT_MS, default 10s)` on all internal +
   FHIR fetches; regression-tested by the SIGSTOP fail-closed test.
3. **De-id recall gap**: Presidio defaults missed 7-digit local US phone
   formats (clinical callback numbers). Fix: fallback pattern recognizers
   (local-phone + MRN-like digit runs) at analyzer startup.
4. **Presidio cold-boot download**: default NLP engine hardcoded
   `en_core_web_lg` (400MB download at container start, breaks offline boot).
   Fix: explicit `NlpEngineProvider` honoring `SPACY_MODEL` (default sm).

**Live tier** (`pytest tests/live`, `LIVE_MODE=extractive`) — records the
GPU-gap as quantified xfail evidence:
- trap refusals 0/10 (gate ≥90% is a generator judgment; extractive mode
  quotes whatever section scored best — a lookalike question cannot be refused)
- citation validity 11/15 = 73% (gate ≥80%; extractive cites top-1 only)
- red-team: 1/3 avoided citation. Conclusion, with numbers: **refusal
  discipline against paraphrase traps requires the GPU stack** — this tier
  must run strict (`LIVE_MODE=gpu`) before any pilot sign-off.

**Load test** (`locust`, ward-traffic shape 70% repeat / 20% unique / 10% ops):

| Run | Users | Reqs | Errors | p50 | p95 | max | req/s |
|---|---|---|---|---|---|---|---|
| loadtest_20u | 20 | 729 | **0** | 18 ms | 29 ms | 300 ms | 6.1 |
| loadtest_50u | 50 | 1840 | **0** | 17 ms | 31 ms | 88 ms | 15.4 |

SLO gates: p50 < 2000 ms ✅ (83× headroom), p95 < 8000 ms ✅ (258× headroom),
error rate < 1% ✅ (0%). Post-load: audit chain `ok: true` over 1,799 audited
records; 99.9% of /process under 100 ms; refusal counter 38% (under the 40%
RefusalFatigue alert — inflated by the synthetic "unique" scenario, which
invents nonsense phrasings that SHOULD refuse).

Caveats, stated plainly: these are **mock-mode, CPU-sandbox numbers**. They
prove the pipeline architecture holds under load with the full
de-id → retrieval → verify → audit path live. The GPU-stack re-run
(`make up-gpu` + the same two commands) remains required evidence for the
final sign-off, where LLM generation latency will dominate.

### Gate 5 re-verification — after full environment reset (2026-09-24, v0.5.1)

The dev sandbox was wiped and rebuilt from the repository alone (clone →
`make bootstrap-native` → tests). Purpose: prove the evidence is
**reproducible from source control**, not an artifact of a hand-configured
environment. Results, same day, fresh machine state:

| Check | Result |
|---|---|
| `make bootstrap-native` | .env generated (random secrets), 4/4 services healthy |
| `make test-integration-native` | **10/10 PASS** (10.5 s) |
| `make test-unit` | **37/37 PASS** |
| `make test-node` | **17/17 PASS** |
| load 20u × 1 min (`loadtest_20u_reset`) | 357 reqs, **0 errors**, p95 27 ms |
| load 50u × 1 min (`loadtest_50u_reset`) | 779 reqs, **0 errors**, p95 26 ms, 13.2 req/s |
| audit chain post-load | `ok: true` over 2,615 records |

One environment-drift bug was caught by this drill: the Makefile's tab
indentation had been silently normalized to spaces between sessions (make
failed with "missing separator" on a fresh checkout of the synced tree),
fixed mechanically and now covered by the bootstrap path failing fast
instead of mid-run.

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
