# Tech Radar — emerging technology assessment (2026-09-24, v0.6.0)

Question asked: *"Do we need more upgrades based on emerging tech — vector
databases, cryptography, …? Keep the ideas open and wide, then assess wisely."*

Method: wide scan first, then one filter — **does it measurably improve patient
safety, evidence quality, or deployment realism for THIS system** (self-hosted,
single GPU, zero-PHI-to-LLM, cite-or-refuse)? Everything else is hype by
definition here. Verdicts: **ADOPT** (build it in), **PILOT** (needs GPU host /
one experiment), **WATCH** (revisit when a trigger fires), **REJECT** (wrong
for this system, with the reason stated so we don't re-litigate it).

## Data & retrieval

| Tech | Verdict | Assessment |
|---|---|---|
| Purpose-built vector DBs (Qdrant, Weaviate, Milvus, pgvector) | **ADOPT — SHIPPED v0.6.1** | Hybrid BM25+vector is already the design; SBERT backend exists behind a flag. Vectors run in **Postgres (pgvector)** inside the existing `data` tier instead of adding a new stateful service: one less thing to secure/backup/patch, same ANN performance at hospital-corpus scale (<100k chunks). `rag-vector-db` service + `rag-vector-data` volume + schema (`deploy/pgvector/init/`) are in the compose stack — **dormant** until the GPU pilot flips `VECTOR_BACKEND=sbert` + `VECTOR_DB_URL`. A dedicated Qdrant becomes rational only past ~1M chunks or multi-tenant scale. |
| Embedding models (MedEmbed, BGE-M3, NV-Embed-v2, gated Sentence-BERT) | **PILOT** | Medical-domain embeddings typically beat generic SBERT on retrieval recall 5–15%. Cheap experiment on the GPU host: swap the encoder, re-run the 208-question gate. The eval harness makes this a data-driven choice, not a vibes choice. |
| Cross-encoder rerankers (bge-reranker, medical cross-encoders) | **PILOT** | Rerank top-20→3 typically adds 5–10% precision and directly feeds the ambiguity-margin gate. Costs ~50–100ms on GPU — affordable vs the 2s/8s SLO budget. |
| SPLADE / learned sparse | WATCH | BM25 is strong for exact clinical terms (drug names, codes); SPLADE's gains are largest on verbose query drift. Revisit if GPU eval shows retrieval misses that BM25+vector both miss. |
| GraphRAG / knowledge-graph RAG (UMLS-linked) | **WATCH → PILOT later** | Real prize for multi-hop clinical questions ("can I give drug X to a patient with condition Y on drug Z" — interaction reasoning). scispaCy entity linking already in the stack is the seed. High effort; only after GPU live gates pass. |
| Agentic RAG (multi-step retrieval, query rewriting, self-RAG) | **WATCH** | The refuse-don't-guess contract makes self-RAG's "retrieve again if unsure" tempting — but each agent step multiplies latency and audit surface. Revisit only with the calibration data from M20 in hand (abstention threshold tells us exactly how often the retriever is the bottleneck). |

## Models & serving

| Tech | Verdict | Assessment |
|---|---|---|
| MedGemma 1.5 (4B multimodal / 27B text) | **PILOT** | Best-documented open medical model family (+5% MedQA, +22% EHRQA over v1, SigLIP for imaging). Same Gemma license terms as current BioMistral plan. Run as a second vLLM model behind the same OpenAI-shaped contract — the mediator never needs to know. The eval + faithfulness + injection suites decide if it replaces BioMistral-7B. |
| Meditron / fully-auditable LLM-CDSS pipelines | WATCH | Licence (Llama-2 Community) is less clean than Apache/BioMistral; training-on-guidelines approach is philosophically what we do with retrieval. Revisit if corpus stewardship lands and we want a domain-adapted base. |
| Structured-output / constrained decoding (vLLM guided JSON, outlines) | **ADOPT — SHIPPED v0.6.1** | Force the generator's answer schema (`covered`/`answer`/`citations`, `deploy/vllm/guided_answer_schema.json`) at the decoding level instead of trusting the prompt. Live in `services/guideline-rag/app/guided_decoding.py` + `GUIDED_DECODING=1` (default): servers that honor `guided_json` cannot emit citation-less answers or free-text refusal drift; servers that ignore it degrade to the legacy text contract; unparseable "structured" output fails closed. Removes an entire hallucination class mechanically. Full behavior table: `deploy/vllm/README.md`. |
| Guardrail models (Llama Guard 3, ShieldGemma, medical safety classifiers) | **PILOT** | Add as a second opinion NEXT to the deterministic injection guard (M19) — never instead of it. Deterministic rules stay the control; the classifier adds recall on novel attacks. Measure false-positive refusal cost on the eval set first. |
| vLLM alternatives (TensorRT-LLM, SGLang) | WATCH | vLLM + prefix caching + guided decoding covers our needs; switching serving stacks is operational churn with no patient-safety delta. |

## Cryptography, privacy & infrastructure

| Tech | Verdict | Assessment |
|---|---|---|
| TLS/mTLS everywhere (real certs, internal mTLS between services) | **ADOPT (roadmap P2 already)** | Not emerging tech — table stakes. Emerging twist worth adopting: **SPIFFE/SPIRE workload identities** instead of static service tokens when the deployment grows past one host. |
| Confidential computing (AMD SEV-SNP, Intel TDX, NVIDIA H100 CC mode) | **PILOT (hardware-dependent)** | Genuine fit: the GPU host processing de-identified questions gets memory-encryption + attestation — a credible answer to "what if the AI host is compromised" in the security questionnaire. H100 CC mode works with vLLM. Adopt when the GPU host is provisioned; zero code change, driver + mode flag. |
| Fully homomorphic encryption (FHE) for LLM inference | **REJECT** | 100–10,000× inference overhead; no FHE LLM serving is production-real. Our threat model already keeps PHI behind the de-id gate — FHE solves a problem we've engineered away. Revisit only if a regulator mandates compute-on-encrypted-EHR. |
| Post-quantum cryptography (ML-KEM hybrid TLS) | **WATCH (2027–2030)** | Audit-ledger integrity is hash-based (SHA-256) and TLS 1.3 PQC hybrids are rolling into standard libraries. Action now: only crypto-agility (no hardcoded cipher pinning) — Caddy/OpenSSL updates carry us. The hash-chained audit log already survives classical attacks; "harvest now, decrypt later" doesn't apply because we ship no ciphertext worth harvesting. |
| Zero-knowledge proofs for audit | **REJECT** | ZK proves computation without revealing data — our audit log is *supposed* to be inspectable by governance. Wrong tool. |
| Differential privacy on eval/feedback data | **WATCH** | Clinician feedback corrections are tiny-N; DP noise would destroy their signal. Relevant only if we ever train/fine-tune on multi-site feedback. |
| Confidential AI inference via TEE-backed attestation in FHIR writeback (provenance) | WATCH | Neat idea: attestation quote as FHIR Provenance — provenance currently records software versions; an attestation is stronger. Park until TEE pilot. |

## Interop & clinical workflow

| Tech | Verdict | Assessment |
|---|---|---|
| MedMemedium/Clinical-bold FHIR `$process-message` + CDS Hooks (`patient-view`, `order-sign`) | **ADOPT (CDS Hooks) — SHIPPED v0.6.1** | CDS Hooks is how real EHRs (Epic, Cerner) surface decision support natively — bigger realism win than any model upgrade. `patient-view` hook = the copilot appears inside the chart: `GET /cds-services` discovery + `POST /cds-services/guideline-copilot-patient-view` on the mediator, riding the SAME pipeline as /process (de-id → RAG → verify → FHIR → audit → review). Prefetch-preferred, FHIR-direct fallback, fail-closed without context. `order-sign` remains future scope once order-context workflows are governed. |
| MCP (Model Context Protocol) tool servers | **WATCH** | Relevant when the copilot grows tools (order lookup, guideline search as tools). Not needed for a single-context answer pipeline; adds an uncontrolled tool layer in a clinical setting — defer until governance has a tool-approval process. |
| TEFCA/QHIN connectivity (US) | WATCH | Network-of-networks data exchange; relevant for the hospital, not the copilot. No action in this repo. |
| Ambient clinical documentation scribes | REJECT (for this repo) | Different product category; ours is cite-or-refuse Q&A, not note generation. |

## The strategic short-list (what we actually do next)

1. **ADOPT now (in-repo, no GPU) — ✅ ALL THREE SHIPPED IN v0.6.1:**
   guided/constrained decoding (schema + parse + fail-closed, live behind
   `GUIDED_DECODING=1`); CDS Hooks `patient-view` facade on the mediator
   (live-verified: discovery, prefetch cards, coverage card, fail-closed
   502); pgvector volume wired into the compose `data` tier + schema
   (dormant until the GPU pilot flips `VECTOR_BACKEND=sbert`).
2. **PILOT in the same GPU session as Gate 5 final sign-off:** embedding swap
   × eval, cross-encoder reranker × eval, MedGemma 1.5-4B vs BioMistral-7B ×
   (eval + faithfulness + injection + calibration). One session, four
   evidence-backed decisions.
3. **WATCH with triggers:** GraphRAG (trigger: multi-hop questions fail the
   eval), agentic retrieval (trigger: M20 shows retrieval-confidence is the
   abstention bottleneck), guardrail classifier (trigger: novel injection in
   the wild), SPIFFE (trigger: multi-host deployment), PQC (trigger: regulator
   mandate), DP (trigger: multi-site training).
4. **REJECT, documented:** FHE inference, ZK audit, ambient scribes as
   in-scope — with reasons above so they stay rejected.

The pattern the radar makes obvious: **the evaluation infrastructure built in
M19–M23 is the multiplier** — every emerging-tech question becomes "run it
against the 208-question gate + faithfulness + calibration and let the numbers
decide". That is the strategic asset; the models are interchangeable.
