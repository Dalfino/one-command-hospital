# Changelog

All notable changes to the One-Command Hospital — Guideline Copilot.
Format: [Keep a Changelog](https://keepachangelog.com/); versions: SemVer.
This is a research project — **nothing here is cleared for clinical
deployment** (see `docs/deployment_readiness.md` for the gate matrix).

## [0.6.1] — Tech-radar ADOPT wave (M24)

All three ADOPT verdicts from `docs/tech_radar.md` implemented, no GPU needed.

### Added
- **Guided / constrained decoding** — `services/guideline-rag/app/guided_decoding.py`:
  the answer contract (`covered` / `answer` / `citations`, citations as typed
  `{corpus_id, section}` pairs) is enforced at the vLLM decoding level via the
  `guided_json` request field instead of trusting the prompt. Prompt mirrors
  the schema when the constraint is on; `parse_guided()` is strict
  (fail-open-to-legacy for free text, fail-closed refusal for unparseable
  "structured" output); `covered:false` is a mechanical refusal.
  Canonical schema mirrored at `deploy/vllm/guided_answer_schema.json`
  (unit test enforces zero drift); behavior table + vLLM version notes in
  `deploy/vllm/README.md`. Env: `GUIDED_DECODING` (default on),
  `GUIDED_JSON_FIELD` (default `guided_json`).
- **CDS Hooks `patient-view` facade** — the copilot surfaces INSIDE any
  CDS-Hooks-capable EHR chart. `services/ai-mediator/cdshooks.js` (pure,
  node-tested) + routes on the mediator: `GET /cds-services` discovery,
  `POST /cds-services/guideline-copilot-patient-view`. Up to 3 questions
  derived from active conditions/medications (prefetch preferred, direct
  FHIR read otherwise, **fail-closed 502** when no context is obtainable).
  Every question rides the same pipeline as `/process` — the `/process`
  handler was refactored into `runPipeline()` so both surfaces share one
  de-id path, one verifier contract, one audit trail, one review queue
  (per-surface metrics labels). Cards: grounded answers = info cards with
  sources; ungrounded = warning cards linking `/review`; refusals = no
  card; all-empty = exactly one deterministic coverage card. Patient
  context is transient input and never reaches cards/logs/audit.
  OpenAPI paths added; integration tier covers discovery, prefetch cards,
  coverage card, validation, audit-chain integrity, fail-closed.
- **pgvector in the compose data tier (dormant)** — `rag-vector-db`
  (`pgvector/pgvector:pg16`) on the internal `data` network with
  `rag-vector-data` volume; schema auto-created on first boot
  (`deploy/pgvector/init/01_schema.sql`: `chunks` (384-d vector, HNSW
  cosine, content_sha idempotent re-sync) + append-only `sync_log`
  provenance). `guideline-rag` joins the data tier with
  `VECTOR_BACKEND`/`VECTOR_DB_URL` env wired; bootstrap generates
  `RAG_VECTOR_DB_PASS`. Nothing reads or writes it until the GPU pilot
  flips `VECTOR_BACKEND=sbert`.
- Mediator version bumped to v0.6.1 surface (`health` unchanged; new
  routes above); OpenAPI 0.6.1.

### Fixed
- **Live finding: question-template filler degrades BM25 specificity.**
  Templated phrasing ("What do the guidelines recommend for managing X?")
  injected corpus-frequent vocabulary that pushed a GARBAGE term above the
  retrieval threshold (verified live) where the bare term correctly
  refused. `questionsFromContext` now passes the bare clinical term as the
  question — documented in code with the evidence trail.
- CDS card summaries no longer open with citation markers / markdown
  section headers ("[ANTICOAG-BRIDGE §1] ## 1."); first-sentence extraction
  strips markers and heading fragments.
- FHIR status concepts are read via `coding[].code` tokens (clinicalStatus/
  verificationStatus), not display names — resolved/refuted conditions are
  now correctly excluded from question generation.

### Verified
- unit **69/69** (9 new guided-decoding tests), node **36/36** (14 new
  cdshooks tests), integration **16/16** (6 new CDS tests) vs live native
  stack; seed eval **98% retrieval** (41/42, unchanged); locust 20u sanity
  p50 19 ms / p95 31 ms (no regression); audit chain ok after CDS traffic.
- Live CDS behavior verified: prefetch → cited info cards; garbage context
  → single coverage card; wrong hook / missing patientId → 400; no
  prefetch + no FHIR → 502 (fail closed).

## [0.6.0] — Safety & governance capability wave (M19–M23) + tech radar

### Added
- **M19 prompt-injection defense** — `services/guideline-rag/app/injection_guard.py`
  (9 instruction-collocation patterns, tuned against clinical-language false
  positives); Gate 0 refuses injected questions, Gate 1b drops poisoned corpus
  chunks before the generator prompt; `rag_injection_blocks_total{surface}`;
  `eval/qa_injection.yaml` (8 hostile items) — **8/8 correct refusals live**.
- **M20 calibration + selective abstention** — `eval/run_eval.py` captures
  per-item confidence/correctness (`eval/scores.jsonl`); `eval/calibrate.py`
  computes 10-bin reliability + ECE, risk-coverage curve, and the
  max-coverage abstention threshold at target risk (`eval/calibration.json`).
  Mock-mode ECE 0.33 with refit-on-GPU caveat recorded.
- **M21 sense-consistency verifier** — `services/verifier/app/context_rules.py`
  (dep-light, unit-testable): flags answers asserting CURRENT patient facts
  whose only cited support is HISTORICAL or FAMILY; guideline conditionals
  deliberately never flagged; `verifier_sense_conflicts_total`; verifier v0.4.
- **M22 clinician review queue + feedback loop** — `services/ai-mediator/review.js`
  (append-log with last-wins compaction; PHI-safe queue records);
  `GET /review/queue`, `POST /review/queue/resolve`, minimal `/review` UI;
  ungrounded answers auto-enrich the worklist; feedback ledger + `tools/feedback_to_eval.py`
  drafts steward-reviewed eval items from corrections; weekly CI drift job
  (full eval + calibration + 100% injection-refusal gate); verified live
  end-to-end (5 real items enqueued by live traffic, resolve → feedback → draft,
  audit chain intact @2,733).
- **M23 claim-level faithfulness** — `eval/faithfulness.py`: decomposes answers
  into claims, checks verbatim numbers, content overlap (≥0.5), and polarity
  against the best-matching cited sentence; wired into every full-mode eval
  report. **First measurement: mean 0.94 over 40 live answers** (extractive).
- **`docs/tech_radar.md`** — wide emerging-tech scan with ADOPT/PILOT/WATCH/
  REJECT verdicts (vector DBs → pgvector; guided decoding; MedGemma 1.5;
  confidential computing; CDS Hooks; FHE/ZK/ambient-scribes rejected with
  reasons; GPU-session short-list).

### Fixed
- `eval/run_eval.py` `RAG_URL` now accepts service root or full endpoint
  (a bare host used to POST `/` → 404 every full-mode request).
- CI: weekly drift schedule added; drift job ports corrected to the test stack.

### Evidence (same-day, live stack)
- Integration 10/10 · unit 60/60 (17 new) · node 22/22 (5 new) · seed full-mode
  35/42 grounded, faithfulness 0.94 · injection 8/8 refused · load sanity
  unchanged (p50 ≈ 21 ms) · audit chain ok @2,733 records.

## [0.5.2] — World-class bar assessment + upgrade roadmap

### Added
- **`docs/world_class_bar.md`** — honest assessment of the project against an
  explicit "top-hospital, no-mistakes" bar: three-line verdict (engineering
  pilot-grade yes; clinical testing = silent-mode synthetic only; generator
  inference evaluation NOT done), scorecard by domain, a complete
  inference-evaluation ledger (evaluated vs not, ranked by risk), and the
  prioritized roadmap — P0 buildable in-sandbox (M19 prompt-injection suite,
  M20 calibration/abstention, M21 ConText verifier, M22 clinician review
  queue + feedback loop, M23 claim-level faithfulness scorer), P1 the single
  GPU-host session (strict live gates → Gate 5 final sign-off), P2
  organizational blockers (corpus stewardship, counsel, pen test, SLA/on-call).
- Fresh evidence same day: integration 10/10, seed eval 41/42 = 98%, unit
  37/37, node 17/17 against the running stack.

## [0.5.1] — Persistence + reproducibility wave

### Added
- **`STATE.md`** — the session anchor: architecture map, milestone ledger,
  gate status, six-dimension gap ledger, remaining blockers, key commands,
  and the recovery protocol for any fresh sandbox/host. The sandbox is
  ephemeral; this file (plus `worklog.md` and this changelog) travels in the
  repo and reconstructs full project context in one read.
- **`tools/bootstrap.sh` + `make bootstrap[-native]`** — fresh host, zero to
  running: generates `.env` with random secrets on first run (never
  overwrites), picks the docker path by default with `--gpu/--observe/--edge`
  profile flags, falls back to the bare-process stack with `--native`, waits
  for all four `/health` endpoints before returning, `--down` to stop.
- **`.dockerignore`** for all five build contexts (4 AI services + synthea) —
  minimal build contexts, no host-file leakage into images.
- **Gate 5 re-verification after a full environment reset** (see
  `docs/deployment_readiness.md`): bootstrap-native → integration 10/10,
  unit 37/37, node 17/17, load 20u/50u 0 errors (p95 27/26 ms), audit chain
  ok over 2,615 records. Evidence: `eval/evidence/loadtest_*_reset.*`.

### Fixed
- Makefile recipe indentation silently normalized from tabs to 8 spaces
  between sessions (make: "missing separator" on fresh checkout) — repaired
  mechanically (`scripts/fix_makefile_tabs.py` in the workspace repo).
- Repository pushed to GitHub as the off-sandbox source of truth (private);
  stale remote history superseded by the canonical M0–M17 local history.

## [0.5.0] — Live Gate 5 evidence run (M17)

### Added
- **`tools/native_stack.sh`** — run the four AI services as bare processes
  with the exact env the test containers get. Where docker is unavailable
  (sandboxes, dev laptops, some air-gapped hosts) the same evidence is
  producible: `make test-integration-native`, `make stack-prod` +
  `make loadtest`. The integration tier is now **probe-first**: it tests
  whichever healthy stack answers at the test ports (docker or native).
- **Live load-test evidence** (`eval/evidence/loadtest_20u|50u.{csv,html}` +
  Gate 5 table in `docs/deployment_readiness.md`): 20 users → 729 reqs, 0
  errors, p50 18 ms / p95 29 ms; 50 users → 1840 reqs, 0 errors, p50 17 ms /
  p95 31 ms; audit hash chain verified over 1,799 records post-load.
  Mock-mode numbers — GPU-stack re-run still required for final sign-off.
- Live tier now records the **generator gap as quantified xfail** under
  `LIVE_MODE=extractive` (trap refusals 0/10, citation validity 11/15 = 73%,
  red-team 1/3) and runs strict gates under `LIVE_MODE=gpu`.

### Fixed — all four found by executing the tiers live (none unit-testable)
- **Mediator↔verifier grounding contract**: the mediator sent citation
  *titles* as verifier sources, so lexical grounding of a full answer against
  a title always failed — the golden path could never verify grounded.
  Citations now carry the quoted section text (`extract_citations` gained an
  optional `section_text` map; built from retrieved sections only).
- **Hung upstream = hung clinician**: no fetch timeout existed anywhere in
  the mediator. A frozen verifier/deid/RAG (GIL stall, black hole — more
  realistic than a dead container) blocked clinician requests forever. All
  internal + FHIR fetches now use `AbortSignal.timeout(UPSTREAM_TIMEOUT_MS)`,
  default 10 s, env-tunable; the fail-closed integration test SIGSTOPs the
  verifier natively to regression-guard it.
- **De-id recall gap**: Presidio defaults missed 7-digit local US phone
  formats (classic clinical callback numbers). Added over-redact fallback
  recognizers (local phone + MRN-like digit runs) at analyzer startup.
- **Presidio cold-boot model download**: default NLP engine hardcoded
  `en_core_web_lg` (400 MB download at container start; breaks offline boot).
  Explicit `NlpEngineProvider` now honors `SPACY_MODEL` (default `sm`).
- Makefile recipe indentation (spaces → tabs) — targets were unparseable.

## [0.4.0] — Commercial-standard & clinical-ready testing wave (M12–M16)

### Added — tests (M12)
- **Three-tier test pyramid** (`tests/`): unit (37 tests, no docker), node
  (17 tests), integration (real containers, docker-gated), live (GPU-gated).
- Integration stack `tests/integration/docker-compose.test.yml` — the four
  AI services in **mock-LLM mode** (guideline-rag extractive fallback) with
  deliberately unreachable Medplum, proving graceful degradation.
- Golden-path E2E: question → de-ID → retrieval → cited answer → verifier →
  audit chain verify → sign-off endpoint.
- **Fail-closed tests**: verifier killed mid-flight → answer returns flagged
  for review, never silently trusted.
- **PHI white-out tests**: planted synthetic identifiers (fake name/MRN/DOB/
  phone) must not survive deid-gate nor reach the FHIR Communication.
- **Live tier**: refusal traps (≥90%), citation validity (≥80%), red-team set
  that must never earn confident cited answers.
- Node audit tests: genesis chaining, tamper → first bad seq, torn line,
  middle-record deletion.

### Fixed
- **guideline-rag would never boot from its own compose file** — corpus path
  resolved to `/guidelines` in-container (parents[2] off-by-one). Introduced
  `GUIDELINES_DIR` env override with a correct container default.
- **Ungrounded answers passed silently**: an answer arriving without
  citations was marked `grounded=true` in the mediator. Now flagged
  `grounded=false — answer carried no citations` + `ungrounded` metric.
- **Extractive fallback lost its citation header** — mock-mode answers were
  unverifiable downstream; fallback now prepends `[CORPUS_ID §N]`.
- Prometheus label values now escaped in mediator metrics (series-injection
  guard).

### Added — observability & ops (M13–M14)
- Structured JSON logs on all 4 services (`{ts, level, service, event,
  request_id, ...}`) with a hard redaction layer — raw question/context/
  answer never reach stdout; `question_sha`/`text_sha` for correlation.
- **X-Request-ID trace propagation**: mediator mints the root id; deid-gate,
  guideline-rag, verifier and Medplum receive and echo it — one request, one
  greppable trace.
- **Edge TLS profile** (`make edge-up`): Caddy terminates HTTPS :8443 for the
  SMART widget, mediator API and OpenEMR pass-through (internal CA in
  sandbox; production checklist item T-1).
- **Backup/restore drills** (`make backup` / `make restore`): guidelines,
  eval evidence, governance docs + the audit ledger, sha256-manifested,
  retention-managed. Restore verifies before touching anything.
- **Load test** (`make loadtest`): locust scenarios shaped like ward traffic
  (70% repeat / 20% unique / 10% ops) against the kill-criteria SLOs.

### Added — commercial hygiene (M15)
- CHANGELOG, CONTRIBUTING, SECURITY disclosure policy, Apache-2.0 LICENSE.
- OpenAPI 3.1 contract for the mediator API (`docs/api/openapi.yaml`).
- SBOM inputs: frozen Python requirements + third-party license register.
- CI extended: node tests on every push; docker integration job.

## [0.3.0] — Hardening wave (M7–M11)

- Compose network segmentation (internal `data` tier), non-root + cap-drop +
  read-only AI services, healthchecks + gated startup, resource limits,
  per-IP token-bucket rate limits, body caps, security headers.
- Hash-chained, append-only audit trail + `/audit/verify`; the QUESTION
  itself now de-identified (was a real leak path).
- Governance docs: model card, security checklist, deployment readiness gate
  (explicit NOT-READY verdict), incident severity ladder, kill criteria.
- Observability profile: Prometheus + 7 alert rules (refusal fatigue,
  ungrounded answers, audit-chain break, p95 latency, 5xx) + Grafana
  dashboard; `/metrics` on all services.
- Eval 52 → **208 questions** (template, keyword-probe, navigation, edition
  drift, 45 hand-verified traps): seed 98% / full **95%** retrieval (BM25),
  CI gate ≥80%.
- Ambiguity-margin refusal gate, TTL+LRU answer cache, `make doctor`
  preflight, CI workflow (eval gates, compile checks, secret scan).

## [0.2.0] — Phase 1 (M1–M6)

- SMART on FHIR widget (Vite + React + fhirclient): ask / sign / escalate.
- Medplum Bot auth: OAuth2 client-credentials + JWT client-assertion (RS384)
  with token cache; `/signoff` closes the human_action loop.
- ConText verifier v0.2: answer-vs-source polarity map, conflict flagging,
  honest engine reporting.
- Hybrid retrieval: alpha·norm(BM25) + (1−alpha)·cosine, title-boosted
  chunks, env-driven, graceful degradation to BM25-only.
- Corpus + eval growth to 3 protocols / 52 questions (98% retrieval).
- Portal story refresh to the one-project architecture.

## [0.1.0] — Scaffold (M0)

- One-command compose stack: OpenEMR, Medplum, OpenHIM, HAPI conformance,
  Synthea patients, vLLM profile.
- deid-gate / guideline-rag / verifier / ai-mediator services.
- Citation-forced RAG with hard `NOT_COVERED` refusal + edition stamping.
- 24-question seed eval (90% retrieval) with refusal traps.
- Architecture doc with kill criteria.
