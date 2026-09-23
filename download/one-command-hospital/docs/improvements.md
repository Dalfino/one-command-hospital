# The six improvements — what we change and how we prove it

## 1. Citation-forced RAG + hard refusal (BioMistral)

- **Upstream:** BioMistral-7B is a fluent medical LLM with no grounding; it
  hallucinates confidently and has no clinical safety alignment.
- **Our change:** retrieval-gated generation. The model sees only top-k corpus
  sections, must cite inline as `[CORPUS_ID §N]`, and low retrieval confidence
  returns `NOT_COVERED` before the LLM is even called.
- **Verify:** eval refusal cases (r01–r04) must refuse; answerable cases must cite
  the expected corpus+section. CI gate: <80% retrieval hit fails the build.

## 2. Guideline version control (Meditron corpus)

- **Upstream:** the ClinicalGuidelines corpus is pretraining fuel — flattened,
  versionless, history-less.
- **Our change:** `guidelines/manifest.yaml` gives every document an id, edition,
  effective/expiry dates. Every answer is stamped; stale editions refuse or warn.
- **Verify:** `GET /health` returns the edition map; citations carry `edition`;
  bump an edition in the manifest and the stamp changes on the next answer.

## 3. NLP-as-verifier (medspaCy + scispaCy)

- **Upstream:** both libraries are positioned as preprocessing/extraction tools.
- **Our change:** they run *after* generation — citation validity, negation
  consistency (ConText in Phase 1), entity/lexical grounding between answer and
  cited source. Preprocessing tech becomes the safety net.
- **Verify:** `POST /verify` flags forged citations and unsupported negations;
  Phase 1 compares heuristic-v0 vs ConText on labelled bad-answer fixtures.

## 4. The AI Mediator pattern (OpenHIM + Medplum)

- **Upstream:** OpenHIM mediators are hand-rolled per integration; Medplum Bots
  are generic. Nothing ties "hospital event → AI → provenanced FHIR writeback"
  into one reusable contract.
- **Our change:** one mediator contract — de-ID → AI → verify → `Communication`
  with provenance + `human_action`. Any future model (sepsis score, MedGemma
  pre-read) becomes a config of the same contract, not a new integration.
- **Verify:** Phase 2 swaps the RAG service for MedGemma behind the same
  `POST /process` with zero contract changes — that swap IS the test.

## 5. Known-answer eval set (Synthea + fixtures)

- **Upstream:** Synthea generates patients; there is no standard way to grade a
  guideline KB end-to-end.
- **Our change:** `eval/qa_seed.yaml` traces every answerable question to a
  corpus id + section, plus refusal traps. The harness scores retrieval hits,
  citation validity, refusal correctness — offline (no GPU) or against the live
  service — and fails CI under threshold.
- **Verify:** `make eval` → `eval/report.md`; retrieval-only mode runs anywhere.

## 6. One-command assembly (all of them)

- **Upstream:** every repo documents itself alone; nobody ships the combined
  hospital, and combined deployment is where hospital AI projects die.
- **Our change:** one compose file, profiles (`gpu`, `patients`, `conformance`),
  ports remapped to a coherent block, `.env.example` with real-variable names,
  and a Makefile whose verbs read like the story (`up`, `patients`, `eval`).
- **Verify:** fresh machine → `cp .env.example .env && make up` → the nine
  services are reachable in ~20 minutes (image pulls aside).
