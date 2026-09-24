# The World-Class Bar — Honest Assessment & Upgrade Roadmap (2026-09-24, v0.5.2)

Question asked: *"Is it commercial-standard? Ready for clinical testing? Done
with inference evaluation? Would a top-5 world hospital run this with no
mistakes and no hiccups?"*

Answered here against that explicit bar, with evidence, and with the
prioritized roadmap that closes the remaining distance. Companion to
`deployment_readiness.md` (gate matrix) and `STATE.md` (session anchor).

---

## 1. The verdict, in three lines

1. **Engineering quality: commercial-standard for a pilot.** The artifact
   discipline (test pyramid 64+ tests, CI-gated eval, hash-chained audit,
   segmented/hardened runtime, OpenAPI/SBOM/docs) is genuinely above most
   internal hospital AI tools.
2. **Clinical testing: ready for silent-mode clinician evaluation on synthetic
   patients only.** Not ready for any real PHI, and not ready for
   point-of-care influence. That is not a software gap — it is a
   content + governance gap (real guidelines, named stewards, counsel).
3. **Inference evaluation: NOT done — and honestly cannot be done here yet.**
   Retrieval and plumbing are well-evaluated; **the generator has never been
   evaluated** because the GPU host has not run it. Every refusal-discipline
   number we have is extractive-mode xfail evidence (0/10 trap refusals).

On "no mistakes, no hiccups": that bar does not exist for any system, medical
or otherwise. World-class means something achievable and better: **measured
failure modes, layered defenses, honest refusal by default, fast detection
and rollback, and a governance loop that catches what engineering cannot
predict.** That standard is reachable. The roadmap below is built for it.

## 2. Scorecard against the world-class bar

| Domain | Bar (top-hospital grade) | Status | The one thing missing |
|---|---|---|---|
| Clinical content | Peer-reviewed, versioned, steward-owned guidelines | ❌ synthetic corpus | Real protocol library + clinical steward sign-off |
| Inference quality | Generator judged on faithfulness, refusal, calibration on GPU stack | ❌ never run | GPU-host live eval (harness ready) |
| Safety testing | Golden path, fail-closed, PHI white-out, red-team floor | ✅ 10/10, re-verified post-reset | Prompt-injection suite (P0 below) |
| Retrieval eval | Gated, versioned, 200+ items, trap taxonomy | ✅ 208q, 95% full / 98% seed | Clinician-validated item expansion |
| Load/SLO | p95 within budget, 0 errors, evidence kept | ✅ 0 errors, p95 26–31 ms (mock) | Re-run under real generation latency (GPU) |
| Security | Least privilege, segmented, rate-limited, TLS, audit | ✅ design-level | Real certs + external pen test + SSO |
| Auditability | Tamper-evident, answer-level decisions recorded | ✅ hash chain, verify endpoint | Off-box immutable shipping |
| Ops | Health checks, metrics, alerts, backup/restore, CI | ✅ | On-call rota, DR drill on live stack, SLA |
| Governance | Model card, kill criteria, change classes, sign-off matrix | ✅ documented | Committee ratification + practiced kill switch |
| Clinician loop | Review queue, feedback → eval set | ❌ flag only | Build the queue + feedback loop (P0 below) |

## 3. Inference-evaluation ledger — exactly what is and isn't done

**Evaluated (evidence in repo):**
- Retrieval hit-rate: 208 items, deterministic, CI-gated — full 95%, seed 98%
- Verifier logic (grounding/citation contract) — unit + integration
- End-to-end behavior: golden path, off-corpus refusal, honest sign-off 502,
  fail-closed under hung verifier, PHI white-out at two surfaces
- SLO under load (mock generation): 0 errors, p95 26–31 ms, audit intact
- Refusal/red-team *harness*: written, gated, versioned

**NOT evaluated (ranked by risk):**
1. **Generator quality — the brain, unjudged.** Trap-refusal (0/10 in
   extractive mode), citation faithfulness under generation, hallucination
   rate, verbosity/latency of BioMistral-7B on vLLM. The harness exists
   (`LIVE_MODE=gpu`); it needs the GPU host.
2. **Calibration / selective prediction.** Today confidence is implicit
   (retrieval margin + verifier boolean). No measured relationship between
   confidence and correctness → no principled "I don't know" threshold.
   Without this, refusal is a guess, not a control.
3. **Adversarial robustness.** No prompt-injection suite yet: malicious
   instructions smuggled in guideline text or FHIR payloads, jailbreak-style
   question framing. A hospital-bound tool must survive hostile input.
4. **ConText semantics in the verifier.** Negation, experiencer (family
   history vs patient), temporality (history of X vs active X) are not yet
   checked — a section retrieved for the wrong temporal sense can still
   "ground" a wrong answer.
5. **Claim-level faithfulness scoring.** Verifier checks the answer lexically
   against cited text; it does not decompose the answer into atomic claims
   and check entailment per claim (RAGAS-style faithfulness).
6. **Clinician-graded accuracy.** No human has ever scored N≥100 answers for
   correctness/usefulness. This is the gold standard every other metric
   approximates.
7. **Fairness probes.** No demographic-framing or plain-language variation
   tests (same clinical question asked about different patient groups).
8. **Drift.** Eval runs are event-driven (CI/human). No scheduled re-run with
   alerting on metric movement.

## 4. Upgrade roadmap

### P0 — buildable in this sandbox, closes real risk (proposed next wave, M19–M23)
| # | Upgrade | What it unlocks |
|---|---|---|
| M19 | **Prompt-injection & red-team suite** — corpus-chunk and FHIR-payload injection fixtures; runtime instruction-pattern guard that refuses-and-logs; adversarial question set in eval | Survives hostile input; audit trail for attempted abuse |
| M20 | **Calibration + selective abstention** — log retrieval margin + verifier score per answer; fit abstention threshold on labeled set; report risk-coverage curve + ECE in eval report | Principled "I don't know"; direct kill-criteria metric |
| M21 | **ConText in verifier** — medspaCy ConText for negation/experiencer/temporality; verifier fails answers grounded on negated/historical/family sections | Closes a real wrong-answer class |
| M22 | **Clinician review queue + feedback loop** — `pending_review` answers land in a worklist (API + minimal UI); approve/reject/correct controls; corrections seed eval set; weekly drift job re-runs seed eval on schedule with alert | The governance loop becomes real, not documented |
| M23 | **Faithfulness scorer** — decompose answer into claims; entail-check each against cited section text (extractive-runnable now, NLI on GPU later); faithfulness % joins the eval report | Hallucination becomes a measured number, not a vibe |

### P1 — needs the GPU host (the single external dependency)
- `make bootstrap --gpu` on the host → vLLM + BioMistral-7B
- `LIVE_MODE=gpu` strict run: trap refusal ≥90%, citation validity ≥80%
- Faithfulness + calibration refit with real generations
- Load test on GPU stack (generation latency dominates) → **Gate 5 final
  sign-off**, the last software gate
- Enable SBERT vector backend + re-run full eval (BM25 baseline preserved)

### P2 — organizational (cannot be coded; must be owned by humans)
- Real guideline corpus + named clinical steward + update cadence
- Regulatory posture: FDA CDS non-device analysis, EU AI Act classification,
  HIPAA BAA/DPIA; counsel review of the model card
- External penetration test with real certs; SOC 2 / HITRUST track
- SLA + on-call rota + executed DR drill; committee ratification of the
  sign-off matrix; practiced kill switch

## 5. Bottom line

The distance to "a top hospital would pilot this" is short and concrete:
P0 (buildable now) + P1 (one GPU session) + one human decision (real
protocols + steward). The distance to "top hospital trusts it at scale" is
honest organizational work (P2) that no repository can do for the project —
but every artifact those committees will ask for already exists here.
