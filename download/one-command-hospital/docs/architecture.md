# Architecture — how the pieces interlock

## Request lifecycle (one question, end to end)

1. **Clinician asks** inside OpenEMR (SMART widget, Phase 1; REST in v0).
2. **ai-mediator** receives `{question, contextText, patientId, userId}`.
3. If note context is attached → **deid-gate** (Presidio + medspaCy rules) scrubs
   identifiers. From here on, no identifier exists in the pipeline.
4. **guideline-rag** retrieves top-3 sections (BM25 over manifest-tagged corpus),
   applies the confidence threshold, builds the citation-forced prompt, calls
   BioMistral-7B via vLLM (OpenAI-compatible), stamps citations with editions.
5. **verifier** checks: citations exist, negations are source-supported, lexical
   grounding ≥ 0.45. Fail → answer is marked `grounded: false` → UI shows a
   review banner; it is never silently discarded or silently trusted.
6. Result is written back to **Medplum** as a `Communication` with provenance
   (sources, edition, model, latency, `human_action: pending_review`).
7. **Audit** record appended (question, response, actor, timestamps). Append-only.
8. Clinician sees answer + citation chips + grounding badge → signs or escalates
   → `human_action` updated. The loop closes with a human in it. Always.

## Safety layers

| Layer | Mechanism | Failure mode |
|---|---|---|
| Privacy | de-id before LLM; Safe Harbor-adjacent entity set | over-redaction acceptable; under-redaction alarmed by finding counts |
| Truth | retrieval threshold + forced citations + `NOT_COVERED` | refusal is the default, not the exception |
| Verification | citation validity, negation consistency, grounding score | `grounded:false` routes to human review |
| Versioning | manifest editions; answers stamped; expiry in manifest | expired edition → refuse or warn (Phase 1 config) |
| Advisory-only | no auto-writeback of orders; human sign-off closes the loop | — |
| Audit | append-only, per-answer provenance | gaps are themselves audit findings |

## Kill criteria (when we stop the pilot)

- Grounded-answer rate < 85% on the 200-question eval at Phase 1 exit.
- Any PHI finding downstream of deid-gate (one strike — root cause, then re-certify).
- Median answer latency > 8 s at steady state after two optimisation passes.
- Clinician trust survey: > 20% "would not use" after 4 weeks.

## Ops notes (v0 rough edges)

- `openhim-console` ships a static config pointing at core API `:8080`; after first
  boot, set its core API target to `localhost:8085` (host remap — Medplum owns 8080).
- First OpenEMR boot runs its setup wizard; FHIR endpoint lives at `/apis/default/fhir`.
- Mediator → Medplum auth is unauthenticated in v0; Phase 1 switches to Medplum
  Bot JWTs (client_credentials), never shared secrets in env.
- vLLM needs ~16GB VRAM for 7B at 8k context (fp16); 4-bit quant fits 10GB.

## Phase plan

- **Phase 0 (done in scaffold):** compose stack, corpus + manifest, eval harness.
- **Phase 1 (4–6 wks):** SMART widget, Bot auth, medspaCy ConText verifier,
  vector retrieval (swap BM25), 200-question eval, staleness alarms.
- **Phase 2:** Orthanc + OHIF in the sandbox; MedGemma imaging pre-read on the same
  mediator contract (proves the "any model as config" claim).
- **Phase 3:** MIMIC-code validation pathway; multi-site federated testbed on
  Synthea-simulated hospitals.
