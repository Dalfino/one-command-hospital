# One-Command Hospital — Guideline Copilot (v0.6.1)

A clinician asks a protocol question **inside the EHR** and gets a cited answer from the
hospital's own guidelines — or an honest refusal. Zero PHI reaches the AI. One GPU. One command.

> **Status: v0.5.1 — reproducible from source control.** Gate 5 evidence re-verified after a full
> environment reset: fresh host → `make bootstrap-native` → integration **10/10**, unit **37/37**,
> node **17/17**, load **0 errors** at 20+50 users (p95 ≈ 26–27 ms, mock mode), audit chain ok
> over 2,615 records. Fresh-host onboarding is one command (`make bootstrap`, or `--native` without
> docker; generates `.env` with random secrets, waits healthy). Project state + recovery protocol
> live in **STATE.md**. Still **NOT cleared for clinical deployment** — see docs/deployment_readiness.md.
> Structured JSON logs with PHI redaction + X-Request-ID tracing; edge TLS, backup/restore drills.
> SECURITY / LICENSE / OpenAPI contract / SBOM register. Eval: **208 questions** — seed **98%**,
> full **95%** (CI gate ≥80%). **NOT cleared for clinical deployment — see
> docs/deployment_readiness.md.**

## The 60-second version

- **OpenEMR** plays the hospital EHR (ONC-certified, native FHIR R4).
- **Medplum** is the FHIR spine where our AI app lives (auth, Bots, SMART launch).
- **OpenHIM** routes clinical events through our **AI Mediator** pattern.
- **Presidio + medspaCy** scrub identifiers *before* anything reaches an LLM.
- **BioMistral-7B** (vLLM, on-prem) answers **only** from retrieved guideline sections,
  with citations like `[ANTICOAG-BRIDGE §3]` — or says `NOT_COVERED`.
- **medspaCy/scispaCy verifier** double-checks the answer against its cited sources.
- **Synthea** fills the hospital with realistic fake patients, so nothing real is ever at risk.
- **HAPI FHIR** validates every resource we write (conformance CI, not runtime).

## Architecture

```
 Clinician (OpenEMR / SMART widget)
        │  question (+ note context)
        ▼
 OpenHIM bus ──► ai-mediator ──► deid-gate (Presidio + medspaCy)   ← PHI dies here
                                     │  scrubbed text
                                     ▼
                              guideline-rag (BM25 → BioMistral via vLLM)
                                     │  cited answer or NOT_COVERED
                                     ▼
                              verifier (entity/negation grounding check)
                                     │
                                     ▼
                       FHIR Communication (+ provenance) → Medplum → EHR UI
                       audit event → append-only log
```

## Quickstart

```bash
cp .env.example .env        # set passwords
make up                     # core stack (no GPU needed for eval-only mode)
make up-gpu                 # adds vLLM serving BioMistral-7B (needs 1× ≥24GB GPU)
make patients               # generate synthetic population into ./data/synthea
make eval                   # run retrieval + grounding eval → eval/report.md
```

| What | Where |
|---|---|
| OpenEMR (first run: setup wizard) | http://localhost:8300 |
| Medplum API | http://localhost:8080 |
| OpenHIM console (admin@openhim.org / openhim-demo) | http://localhost:9000 |
| de-id gate / RAG / verifier / mediator | :8100 / :8101 / :8102 / :8103 |
| vLLM (OpenAI-compatible) | :8104 |
| HAPI FHIR (conformance profile) | :8105 |

## The six improvements (vs. upstream)

| # | Improvement | Upstream today | Ours |
|---|---|---|---|
| 1 | Citation-forced RAG + hard refusal | BioMistral answers freely, hallucinates confidently | Answers only from retrieved sections; must cite; else `NOT_COVERED` |
| 2 | Guideline version control | Meditron corpus = pretraining fuel, no versioning | Every answer stamped with corpus id + edition + section |
| 3 | NLP-as-verifier | medspaCy/scispaCy used for preprocessing | Used *post-generation*: citation validity, negation & entity grounding |
| 4 | AI Mediator pattern | OpenHIM mediators are hand-rolled per project | One reusable contract: event → de-ID → AI → FHIR writeback w/ provenance |
| 5 | Known-answer eval set | Synthea covers patients, nobody covers KB eval | 20+ seeded Q/A pairs traced to protocol sections, scored in CI |
| 6 | One-command assembly | Good individual docs, no combined story | This repo: `make up` |

## Repo map

```
guidelines/        seed knowledge base (SYNTHETIC protocols + manifest w/ editions)
eval/              known-answer QA (52 pairs) + runner (retrieval & grounding metrics)
services/
  deid-gate/       FastAPI + Presidio PHI scrubber          :8100
  guideline-rag/   hybrid retrieval + citation-forced RAG    :8101
  verifier/        medspaCy ConText grounding checks         :8102
  ai-mediator/     OpenHIM mediator, JWT auth, /signoff      :8103
smart-app/         SMART on FHIR widget (Vite+React, build green)
portal/            program website (Next.js 16) — the stakeholder story
tools/synthea/     synthetic patient generator image
docs/              architecture.md, improvements.md
```

## Safety model (non-negotiables)

1. De-ID **before** LLM contact — the model never sees identifiers.
2. Hard refusal when retrieval confidence is low. No source, no answer.
3. Advisory-only outputs; a human always acts. Every answer carries provenance.
4. Append-only audit log: question, sources, edition, model+version, response, action.
5. Staleness alarms: answers refuse (or warn) when a guideline edition is expired.
6. Kill criteria defined in `docs/architecture.md` — the failure story is designed.

## Honest limitations (Phase 1 in progress)

- Remaining Phase 1 wiring: SMART iframe launch registration in OpenEMR, OpenHIM
  mediator registration, vector backend on by default (currently BM25 unless
  `WITH_SBERT` build arg), eval set 52 → 200.
- `openhim-console` may need its core-API endpoint tweaked after first boot (noted in compose).
- Seed protocols are **synthetic**, authored for testing — never medical advice.

## Roadmap

1. **Phase 0 (done):** stack up, eval harness green, synthetic hospital populated.
2. **Phase 1 (complete):** SMART widget ✅ · Bot JWT auth ✅ · ConText verifier ✅ ·
   hybrid retrieval ✅ · eval 208 questions ✅ · hardening wave M7–M11 ✅ ·
   test pyramid + CI integration gate M12–M16 ✅ · **live integration + load evidence M17 ✅** ·
   OpenHIM registration ⬜ · live-mode trap-refusal gate ⬜ (GPU stack).
3. **Phase 2:** real hospital protocols + steward sign-off, live-mode eval, TLS +
   pen test, Orthanc + OHIF imaging layer, MedGemma pre-read (Recipe B).
4. **Phase 3:** MIMIC-code validation pathway, federated testbed, device layer.

## Milestones

| M | Commit | What landed |
|---|---|---|
| M0 | `b8aea4d` | v0 scaffold — compose stack, corpus, eval (18/20), 4 services |
| M1 | `0a109b8` | SMART on FHIR widget — vite build green, ask/sign/escalate loop |
| M2 | `11bbaa2` | Medplum Bot JWT auth + `/signoff` audit-loop endpoint |
| M3 | `ce51fea` | Verifier v0.2 — medspaCy ConText polarity checks |
| M4 | `406d6d8` | Hybrid retrieval (BM25 + optional SBERT), title-boosted chunks |
| M5 | `2c05ca2` | 3 protocols, 52-question eval, **98% retrieval** (CI gate 80%) |
| M6 | portal | Program website (Next.js) with the full flagship story |
| M7 | hardening | Compose segmentation (internal data net), non-root + cap-drop + read-only AI services, healthchecks, resource limits, `.env.example` |
| M8 | governance | Hash-chained audit trail + `/audit/verify`; question de-ID fix; model card, governance charter, security checklist, **deployment readiness gate** |
| M9 | observability | `make observe` — Prometheus + 7 alert rules (refusal fatigue, ungrounded, audit-chain) + Grafana dashboard |
| M10 | accuracy | Eval 52 → **208** (seed 98%, full **95%**), ambiguity-margin gate, trap sanity probe |
| M11 | ops | `make doctor` preflight, CI workflow (eval gates + secret scan), TTL answer cache, vLLM prefix caching, Dockerfile fixes |
| M12 | testing | **Test pyramid**: 37 unit + 17 node tests; docker integration tier (golden path, fail-closed, PHI white-out) + GPU live tier; mock-LLM mode. **Found + fixed: rag corpus path (never booted), ungrounded answers passing silently, fallback losing citations** |
| M13 | tracing | Structured JSON logs (PHI-redacting) + `X-Request-ID` root trace minted by mediator, propagated deid→rag→verifier→FHIR |
| M14 | edge/ops | Caddy TLS profile (`make edge-up` :8443), verified backup/restore drills (audit ledger included), locust load test vs kill-criteria SLOs |
| M15 | hygiene | CHANGELOG, CONTRIBUTING, SECURITY policy, Apache-2.0 LICENSE, OpenAPI 3.1 contract, SBOM + license register, CI: node tests + docker integration job |
| M16 | sync | README/portal truth sync, v0.4.0, worklog |
| M17 | evidence | **Live Gate 5 run**: integration 10/10 vs native stack, locust 20u+50u (0 errors, p95 31 ms, mock), audit chain intact @1,799 records, live-tier GPU-gap quantified (0/10 traps, 73% cites in extractive). **Found + fixed: verifier grounding contract, no upstream timeout (hung verifier hung clinician), 7-digit phone de-id gap, Presidio lg cold-boot download**. `make test-integration-native` + `make loadtest` now docker-optional |
| M18 | persistence | **Repo = source of truth**: pushed to private GitHub; `STATE.md` session anchor (recovery protocol + gap ledger); `make bootstrap[-native]` fresh-host onboarding (random-secret .env, health-wait); `.dockerignore` ×5; **Gate 5 re-verified post-reset** (10/10, 37/37, 17/17, 0 load errors p95 26–27 ms, audit ok @2,615) |
| M19–M23 | safety+governance | **Injection guard** (Gate 0 question screen, Gate 1b poisoned-chunk drop, 8/8 live refusals) · **calibration** (ECE + risk-coverage + abstention threshold, mock-mode caveat) · **sense-consistency verifier** (historical/family conflict class) · **clinician review queue + feedback→eval loop** (live E2E verified, weekly CI drift job) · **claim-level faithfulness** (first measurement 0.94) · `docs/tech_radar.md` (ADOPT/PILOT/WATCH/REJECT emerging-tech scan) |
| M24 (v0.6.1) | tech-radar ADOPT wave | **Guided decoding** — answer schema (`covered`/`answer`/`citations`) enforced at the vLLM decoding level, not just the prompt; legacy servers degrade, malformed structured output fails closed (`deploy/vllm/`) · **CDS Hooks `patient-view`** — the copilot appears INSIDE the chart: `GET /cds-services` + hook service riding the same pipeline (de-id → RAG → verify → FHIR → audit → review), prefetch-preferred, fail-closed without context; refusals emit no card, all-empty gets one coverage card · **pgvector in the data tier** — `rag-vector-db` + schema in compose, dormant until the GPU pilot flips `VECTOR_BACKEND=sbert`. Live-verified: unit 69/69, node 36/36, integration 16/16 (6 new CDS tests), seed eval 98% retrieval, load p95 31 ms. Found + fixed live: question-template filler words degrade BM25 specificity (bare clinical terms now the query contract) |

## Licensing note

Upstream components keep their licenses: OpenEMR (GPL), Medplum (Apache-2.0),
OpenHIM (MPL-2.0), Synthea (Apache-2.0), HAPI (Apache-2.0), Presidio (MIT),
medspaCy (MIT), scispaCy (Apache-2.0), BioMistral (Apache-2.0), Meditron corpus
(Llama-2 community terms — corpus used for research here). Verify before any commercial use.
