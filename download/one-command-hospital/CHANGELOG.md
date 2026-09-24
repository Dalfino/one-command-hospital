# Changelog

All notable changes to the One-Command Hospital — Guideline Copilot.
Format: [Keep a Changelog](https://keepachangelog.com/); versions: SemVer.
This is a research project — **nothing here is cleared for clinical
deployment** (see `docs/deployment_readiness.md` for the gate matrix).

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
