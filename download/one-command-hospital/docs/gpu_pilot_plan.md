# GPU Host Plan — Pilot First, Free First (v0.6.2)

**Status:** DECIDED · **Owner note:** this document operationalizes the PILOT
tier of `docs/tech_radar.md` — the one GPU session that answers four PILOT
verdicts (embedding swap, cross-encoder reranker, MedGemma 1.5 vs BioMistral-7B,
guardrail classifier) *and* carries the strict `LIVE_MODE=gpu` live gates.
Runnable form: `gpu_pilot/gpu_pilot_notebook.ipynb` (Kaggle T4 preferred,
Colab T4 alternate).

---

## 1. The question, answered directly

**Does the GPU session have to run on the local computer / local server?**
No. The stack is host-agnostic: four services on localhost ports (8100–8103
prod shape), all gates are local make targets or pytest invocations against
those ports, and every evidence artifact is a file under `eval/evidence/`.
Nothing in the Gate-5 definition requires a specific machine — it requires a
CUDA host that can serve the generator and enough session stability to finish
a loadtest without dying mid-run.

**Can we try free GPU first?** Yes — and that is the right sequencing, because
the free run is a *pilot*, not the sign-off. But the two options first named
for this are the wrong free options:

- **GitHub Codespaces** has **no free GPU**. The personal free tier is 120
  core-hours/month of 2-core CPU; GPU machine types are paid-only. Codespaces
  remains a fine free CPU host for dev and CPU-shape gates, but it cannot
  serve the GPU pilot for free.
- **HuggingFace Spaces** free hardware is **CPU-only** (2 vCPU / 16 GB). GPU
  requires paid hardware (T4 ≈ $0.40+/hr) or ZeroGPU (PRO quota, request-time
  allocation on ephemeral workers). ZeroGPU is architecturally hostile to our
  shape: it allocates an H200 slice *per request* — a persistent 4-service
  stack plus a sustained loadtest does not fit that model. HF Spaces remains
  the home for the *public demo later* (a Docker Space exposing the mediator),
  not for gates.

The free GPUs that actually exist are in **notebook VMs**: **Kaggle** (T4×2 or
P100, 30 GPU-hrs/week, sessions up to 12h, supports headless background runs)
and **Google Colab free** (T4 16GB, session-limited, tab must stay open). Both
suffice for the pilot because of one lucky fact: **the target generator,
BioMistral-7B, fits a single free T4** — in 4-bit (GPTQ/AWQ ≈ 4–5 GB weights)
with generous KV-cache headroom (fp16 ~14 GB is addressable but tight; 4-bit
is the pilot default).

## 2. Host options matrix

| Host | Free GPU? | GPU / VRAM | Session shape | BioMistral-7B fits? | Loadtest realism | Verdict |
|---|---|---|---|---|---|---|
| **Local computer / server** | n/a (owned) | any ≥8GB; plan assumed ≥24GB | persistent | fp16 on 24GB; int4 on 8GB+ | best (dedicated) | **Gold standard for Gate-5 sign-off** |
| **Kaggle Notebooks** | ✅ 30 GPU-hr/wk | T4×2 (16GB×2) or P100 | ≤12h; headless "Save & Run All" | ✅ int4 easily | shared-VM → pilot-grade | **Recommended free pilot host** |
| **Google Colab (free)** | ✅ best-effort | T4 16GB | ~hours; tab must stay open | ✅ int4 | shared-VM → pilot-grade | Alternate pilot host |
| **GitHub Codespaces** | ❌ | GPU = paid only | free 120 core-hr/mo CPU | ❌ (no GPU) | n/a | Free CPU dev host only |
| **HF Spaces** | ❌ | T4 paid ≈$0.40/hr; ZeroGPU ephemeral | app-shaped, 1 exposed port | paid only | ZeroGPU ≠ loadtest | Public demo later, not gates |
| **RunPod / Vast.ai spot** | ❌ but ~$0.25–0.50/hr | RTX 3090/4090 24GB | dedicated VM | fp16 or int4 | near-production | **Paid fallback for sign-off (~$2–5 total)** |
| **Lightning.ai / Modal** | free credits | T4-class | studio / serverless | ✅ int4 | varies | Third-line fallback |

Reading: free-first is real, but it routes through Kaggle/Colab. Codespaces
and HF Spaces keep legitimate roles elsewhere (free CPU host; future public
demo) — they are just not the free GPU pilot.

## 3. Tiered execution plan

**Tier 1 — Free pilot (the PILOT-bundle run).**
Host preference: **Kaggle T4** (headless runs, evidence lands in notebook
output) → fallback **Colab T4** (tab stays open for 1–2h). Engine: vLLM
serving BioMistral-7B in 4-bit (GPTQ primary, AWQ fallback),
`max_model_len=4096`, `gpu_memory_utilization≈0.90`. Stack: native runner —
`LLM_URL=http://127.0.0.1:8099/v1 bash tools/native_stack.sh up-prod` (the
v0.6.2 `LLM_URL` override; notebook VMs have no Docker daemon, which is what
the native path was built for). Guided decoding stays on
(`GUIDED_DECODING=1`; set `GUIDED_JSON_FIELD=structured_outputs` for current
vLLM builds per `deploy/vllm/README.md`). Gates, in order:

1. `make test-unit` · `make test-node` · `make test-integration-native`
2. `RAG_URL=http://127.0.0.1:8101 make eval` (seed, full mode) and
   `RAG_URL=http://127.0.0.1:8101 make eval-full` (208 questions vs the live
   GPU-backed stack)
3. **Strict live gates:** `RAG_URL=http://127.0.0.1:8101 LIVE_MODE=gpu
   python -m pytest tests/live -m live` → **trap refusal ≥90%**, **citation
   validity ≥80%**, red-team floor held
4. `make loadtest LOCUST_USERS=20 LOCUST_RUN_TIME=2m` (pilot-grade latency
   ONLY — shared VM) · `make audit-verify`

Tier-1 success = strict functional gates met. Latency numbers collected but
explicitly non-authoritative.

**Tier 2 — Gate-5 final sign-off (definition unchanged).**
Host: **local ≥24GB GPU server if available** (matches deployment reality,
air-gap story, dedicated hardware → authoritative p95). If no local GPU: a
**RunPod/Vast 3090/4090 spot for one session ≈ $1–5 total**. What changes vs
Tier 1: only the loadtest evidence becomes authoritative; functional gate
results remain valid as functional metrics.

**Tier 3 — later, separate track:** HF Docker Space on paid T4 as the public
demo / portal deep-link, after sign-off.

## 4. Evidence protocol for free/shared VMs

Free-VM evidence is welcome but must be labeled so Gate-5 cannot be inflated
by accident. Every evidence tarball produced on a free host ships with a
`HOST_manifest.json` in `eval/evidence/`: provider, GPU model, shared-VM
flag, timestamp, model served, and the fixed caveat line **"free shared-VM —
pilot-grade evidence, not Gate-5 sign-off"** for any latency-bearing
artifact; sha256 accompanies the tarball. Functional metrics (trap refusal,
citation validity, red-team floor, unit/node/integration results) are
latency-independent and stand as valid pilot evidence. The Gate-5 sign-off
definition stays exactly as approved — nothing is waived; only *whose*
loadtest numbers count changes.

## 5. The PILOT experiments in the same session (radar short-list item 2)

Each is a re-run of the same notebook against the already-running stack, one
evidence pack per decision:

- **MedGemma 1.5-4B-it vs BioMistral-7B:** set `PILOT_MODEL=google/medgemma-1.5-4b-it`
  in the notebook (gated — accept license on the model page; HF token at the
  prompt), re-run cells 5→9. Decision = strict gates + eval-full + faithfulness
  delta.
- **Embedding swap** (MedEmbed / BGE-M3 vs generic SBERT): flip
  `VECTOR_BACKEND=sbert` + embedding model env on `guideline-rag`, re-run
  eval-full. Needs the same 1-line env-override treatment `LLM_URL` got
  (small follow-up change when this experiment runs — noted here so it isn't
  forgotten).
- **Cross-encoder reranker:** top-20→3 rerank in front of the ambiguity-margin
  gate; measure eval-full precision delta + added latency against the 2s/8s
  SLO budget.
- **Guardrail classifier** (Llama Guard 3 / ShieldGemma): second opinion NEXT
  to the deterministic injection guard (never instead); measure false-positive
  refusal cost on the eval set first.

## 6. Risks and fallbacks

- **No T4 available on Colab right now** (common): retry or switch to Kaggle
  (P100/T4×2). Both dead → Lightning.ai credits → paid spot.
- **Kaggle weekly quota exhausted** (30 GPU-hr): the pilot needs ~1–2 GPU-hr;
  exhaustion unlikely; fallback chain applies.
- **vLLM kernel support on T4 (SM75):** GPTQ and AWQ GEMM kernels run on
  Turing (marlin auto-fallback). fp16 is the fallback only on ≥24GB.
- **OOM on 16GB:** enforce 4-bit, `max_model_len=4096`,
  `gpu_memory_utilization=0.90`, `enforce_eager=True`.
- **`guided_json` deprecation warnings** on current vLLM: set
  `GUIDED_JSON_FIELD=structured_outputs` (the notebook pre-sets this) — no
  code change either way, per `deploy/vllm/README.md`.
- **Interface drift:** the notebook's discovery cell prints STATE.md, the
  Makefile, the native runner and the guided-decoding README before wiring
  anything, and instructs to STOP and reconcile rather than force through.
- **Credentials:** the notebook pulls the private repo and (optionally) gated
  models at runtime; tokens are entered via `getpass` (input-hidden, never
  written to disk), inline-only per the standing protocol. Rotate anything
  ever pasted into chat.

## 7. What shipped in v0.6.2 to enable this

- `tools/native_stack.sh`: `LLM_URL` env override for `up-test`/`up-prod`
  (previously the generator URL was hardcoded unreachable = mock mode only).
- `gpu_pilot/gpu_pilot_notebook.ipynb`: the runbook above in executable form
  (introspection → clone → interface discovery → deps → vLLM 4-bit → native
  GPU stack → full gate ladder → labeled evidence harvest → teardown).
- This document.
