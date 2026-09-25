# GPU Tier-1 pilot — Kaggle T4 x2, 2026-09-25 (kernel v6-v12)

**Verdict: pipeline PROVEN end-to-end on the free tier; citation gates PASS;
refusal gates FAIL on 7B generators (quantified) — decision points below.**

Evidence caveats per protocol: `free shared-VM — pilot-grade evidence, not
Gate-5 sign-off` (HOST_manifest.json, gate5_signoff=false).

## Final run (v12) — snapshot 3e718a9, model BioMistral-7B-Zephyr-Beta-SLERP-AWQ

| Gate | Result | Numbers |
|---|---|---|
| GPU integration end-to-end (dataset restore -> vLLM int4 -> native GPU stack -> gates) | PASS | snapshot sha256-verified; vLLM :8099 healthy; 8100-8103 healthy |
| eval seed (52q, live GPU) | PASS | retrieval 41/42 (98%), grounded citations **39/42 (93%)** |
| eval full (208q, live GPU) | PASS | retrieval 146/153 (95%), grounded citations **143/153 (93%)** |
| LIVE strict: citation validity >=80% | **PASS** | 15-question sample vs expected corpus+section |
| LIVE strict: trap refusal >=90% | **FAIL** | seed live 2/10; full set 12/55 — generator says covered=true on out-of-corpus questions |
| LIVE strict: red-team floor | **FAIL** | 1/3 (apixaban-dialysis) got a *cited* answer — clinically sane text, but the contract demands refusal |
| loadtest 20u x 2m (pilot-grade) | exit 2 | 7 deterministic 502s on /process; p50 ~35-40ms, p95 ~180ms (shared VM) |
| unit / node / audit-verify | PASS | exit 0 |
| integration-native (mock shape) | PASS | exit 0 (v10 lesson: live LLM_URL leaked into the test stack — now reset per documented mock mode) |

## What it took (ops findings, all fixed and shipped)

1. **Run config**: the kernel must carry the accelerator (`machine_shape:
   NvidiaTeslaT4`) — a CPU-attached run dies at `nvidia-smi` (user's manual v1).
2. **Deps parity**: native mode needs the services' requirements + the spacy
   `en_core_web_sm` model + locust (Dockerfile parity) — deid-gate hard-imports
   Presidio, no fallback.
3. **Gate order**: `test-integration-native` cleanup (`native_stack.sh down`)
   kills the -prod pids too — prod-stack gates must run FIRST (run-4 lesson).
4. **Model-name wiring**: vLLM must `--served-model-name` exactly
   `LLM_MODEL` (native_stack.sh forwards it since v0.6.3) or every call 404s
   into the silent extractive fallback (4ms answers = the tell).
5. **Guided wire shape**: `structured_outputs` needs the `{"json": schema}`
   wrapper; the raw schema is 400-rejected. Wire shape is now PROBED at
   runtime before boot. `llm_call_failed` is logged (no more silent fallbacks).
6. **Dataset determinism**: Kaggle auto-extracts .tar.gz (async, inconsistent
   layout, stale trees linger) — the snapshot ships as a sha-verified `.bin`
   carrier, extracted locally by the kernel (provenance byte-exact).
7. **Citation provenance** (the semantic fix): 7B generators answer well but
   emit no inline markers and empty citations arrays (0 citations across 195
   live GPU answers while retrieval hit 95-98%). `citations_for_answer()`
   merges answer-text markers + generator claims + retrieved sections
   (unbacked claims dropped) — citations are now honest PROVENANCE of what
   the generator saw; the verifier stays the per-claim grounding judge.

## Decisions this evidence forces

1. **Generator choice is a real decision now**: Zephyr-SLERP-AWQ beats base
   BioMistral-AWQ (refusals 0/10 -> 2/10 seed; richer answers) but both fail
   abstention. Options: MedGemma-1.5-4b-it (gated: HF license + token;
   `PILOT_MODEL` switch already in the runbook) on a Tier-2 host, a >=13B
   instruct, or verifier-synthesized refusal (fail-closed answer validation)
   as a mechanical mitigation.
2. **Gate-5 sign-off** still needs a stable host (local >=24GB or ~$2-5 spot);
   latency numbers here are pilot-grade only.
3. **Loadtest 502s** (7 deterministic, /process) — investigate with the
   native service logs shipped in this pack.

Raw artifacts: HOST_manifest.json, gate_summary.json, vllm_8099_tail.log,
native_*.log, loadtest_20u_*; full kernel logs on the Kaggle kernel page
(aminurhakim/gpu-pilot-notebook, versions 6-12).
