# Model Card — Guideline Copilot (system card v1.0)

> Modeled on the standard model-card template; this is a SYSTEM card: the risky
> unit is not the LLM alone but the retrieval + generation + verification pipeline.

## Model details

- **System**: citation-forced RAG copilot. BM25(+optional SBERT) retrieval over
  the hospital's own guideline corpus → BioMistral-7B generation with inline
  citation requirement → ConText/heuristic verifier → FHIR writeback with
  provenance and mandatory clinician sign-off.
- **Base model**: `BioMistral/BioMistral-7B` (Apache-2.0), continued-pretrain of
  Mistral-7B-Instruct on PubMed Central. Serving: vLLM, temperature 0.1,
  max_tokens 500, prefix caching enabled, max_model_len 8192.
- **Date**: card version 1.0, 2026-09. Corpus editions in `guidelines/manifest.yaml`.

## Intended use

- **In scope**: adult inpatient clinical staff asking operational questions that
  the hospital's OWN approved protocols answer ("what does OUR protocol say
  about X"). Answers are advisory, cite specific protocol sections, and require
  clinician sign-off.
- **Out of scope (hard refusals by design)**: diagnosis, dosing outside corpus,
  pediatric/ICU/emergency pathways unless the corpus covers them, anything not
  in the corpus. The system refuses (`NOT_COVERED`) rather than generalizing.

## Training data & corpus

- Base model: PubMed Central (public biomedical literature) — provenance per
  BioMistral paper. No hospital data was used for training.
- Runtime knowledge: hospital-authored guideline corpus only. Currently 3
  SYNTHETIC protocols (anticoagulation bridging v3.0, sepsis screening ed.2,
  inpatient glycemic control v1.0) marked `synthetic: true` in the manifest.
  Real protocols require Corpus Steward approval before ingestion (governance §3).

## Eval results (2026-09, BM25-only retrieval mode)

| Suite | Items | Result |
|---|---|---|
| Seed (hand-written) | 42 answerable + 10 traps | **98%** retrieval (41/42) |
| Full (`qa_full.yaml`) | 153 answerable + 55 traps | **95%** retrieval (146/153) |
| Refusal behavior (traps) | 55 | defined + BM25-probed; live refusal pass pending GPU run |

CI fails below 80% retrieval on either suite. Live-mode grounding target: ≥85%.

## Limitations

1. Retrieval is lexical-first; paraphrase-heavy or synonym-distant questions can
   miss (3 misses in the current full set — listed in `eval/report_full.md`).
2. The verifier is rule/ConText-based, not a semantic NLI model; subtle
   numeric or entity swaps inside a cited section are imperfectly caught.
3. Question + note text is de-identified by Presidio before any model call;
   recall is not perfect — fail-safe is over-redaction, not zero-redaction.
4. Corpus coverage is tiny by design (3 protocols). Refusal rate on real-world
   questions will be HIGH until the corpus grows — this is correct behavior and
   the refusal-fatigue alert exists precisely for the temptation to loosen it.
5. Single-host compose deployment; no HA; evals are retrieval-mode in CI
   (live-mode eval requires GPU and is a release-time gate).

## Ethical & safety considerations

- Zero-PHI-to-AI architecture: identifiers are scrubbed before any model call;
  the audit trail stores scrubbed questions only.
- Human oversight: every answer is advisory and signed off; sign-off state is
  tracked on the FHIR resource and audited.
- Equity: monitoring includes stratified refusal/escalation rates (governance §4).
- Environmental: 1×24 GB GPU, prefix caching; quantization path documented for
  smaller cards.

## Recommended re-eval cadence

Every corpus change, every model change, every retrieval/prompt change (CI
enforced), plus a quarterly full re-run including live-mode trap refusal.
