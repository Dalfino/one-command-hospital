# AI Governance Framework — Guideline Copilot

> One page of philosophy, then the machinery. The philosophy: **an AI that talks
> to clinicians about patient care is governed like a formulary drug** — known
> composition (model card), known batch records (audit trail), a pharmacist who
> can say no (verifier + mediator), a committee that recalls it (kill criteria),
> and an incident log when something goes wrong (this document, §Incident response).

Status: **draft for committee ratification** — this document ships as code; the
committee ratifies it as policy at the first meeting.

---

## 1. Roles

| Role | Who (pilot) | Accountability |
|---|---|---|
| AI Governance Chair | named sponsor | Signs Gate 4; owns this document; chairs incident reviews |
| Clinical Sponsor | department head | Owns intended-use fitness; signs Gate 0 |
| Quality & Safety Lead | quality director | Owns the eval set's clinical validity; signs Gate 1 |
| IT Security Lead | CISO delegate | Owns threat model, pen test, secrets; signs Gate 2 |
| Platform Lead | engineering owner | Owns uptime, backups, observability; signs Gate 3 |
| Corpus Steward | P&T / Quality committee delegate | Approves every guideline edition before ingestion |
| Answer Ombudsman | rotating senior clinician | Samples 20 answers/week; files discrepancies |

No role may be held by the person who built the system (separation of duties:
the builder documents, the committee decides).

## 2. What is governed

1. **The corpus** — every guideline document, its edition, effective date, expiry,
   and approver (`guidelines/manifest.yaml` is the register).
2. **The model** — BioMistral-7B (or successor) pinned by digest in the model
   card; changing it is a *major* change (§5).
3. **The retrieval config** — thresholds, margins, engine (BM25/SBERT alpha).
4. **The prompts** — versioned with the repo; prompt changes are changes to
   clinical behavior and go through review.
5. **The verifier rules** — ConText configuration and grounding thresholds.
6. **The audit trail** — append-only, hash-chained; who may read it, never who
   may edit it. Nobody may edit it.

## 3. Change control

| Change class | Examples | Path |
|---|---|---|
| Minor | docs, dashboards, non-clinical tooling | normal PR |
| Moderate | retrieval config, verifier thresholds, prompt wording | PR + Quality Lead approval + eval-full green |
| Major | new corpus edition, model swap, new clinical domain | PR + Corpus Steward + committee vote + re-run eval + 2-week shadow mode |

Shadow mode (major changes): the new config answers real traffic in parallel,
outputs recorded but not shown to clinicians; committee reviews divergence rate
before promotion.

## 4. Monitoring & the numbers we watch

The Grafana dashboard (`observe/grafana/dashboards/copilot.json`) and the alert
rules (`observe/prometheus/alert_rules.yml`) encode the committee's risk appetite:

| Signal | Threshold | Meaning |
|---|---|---|
| Refusal rate | >40% for 10 min | refusal fatigue → corpus/retrieval drift; clinicians will bypass us |
| Ungrounded answers | any sustained 5 min | dangerous direction → investigate immediately |
| p95 latency | >8 s for 15 min | trust erosion; kill-criteria threshold is median >8s |
| 5xx rate | >5% for 10 min | reliability |
| Audit chain broken | any | SEV-2 (§6) |
| Service down | 2 min | paging |

Weekly (Ombudsman): 20 sampled answers scored against source; discrepancy rate
trended at each committee meeting. Monthly: refusal/escalation rates stratified
by ward and shift (equity check).

## 5. Model registry

Current: `BioMistral/BioMistral-7B` (Apache-2.0) via vLLM, temperature 0.1,
max_tokens 500, prefix caching on. The registry entry must record: model id,
image digest, serving flags, eval scores at adoption (seed + full), and the
committee minute that approved it. Any successor model repeats the process —
including the 4 refusal-trap categories passing **in live mode**.

## 6. Incident response

Severity ladder:

- **SEV-1 — PHI exposure or hallucinated clinical instruction accepted.**
  Kill switch immediately (`docker compose stop ai-mediator guideline-rag`),
  committee chair + CISO + clinical sponsor within 1 hour, preserve audit log.
- **SEV-2 — audit chain broken, verifier offline >30 min, refusal rate 100% >1h.**
  Disable affected path, root-cause within 1 business day.
- **SEV-3 — alert-threshold breaches without patient impact.** Ticket + weekly
  review.

Every incident: timeline, root cause, eval additions that would have caught it
(added to `eval/`), and a committee minute. **An incident without a new eval
case is not closed.**

## 7. Kill criteria (restated from architecture.md)

These are pre-agreed; activation is automatic, not debated per-incident:

- Grounded-answer rate < 85% over any rolling week → disable AI output, run extractive citations only
- Any confirmed PHI reaching the LLM path → immediate SEV-1 stop
- Median answer latency > 8 s sustained → withdraw from workflow
- Clinician trust survey < 80% → pause and re-design UX before resuming

## 8. Regulatory posture (summary; counsel confirms)

- **EU AI Act**: likely high-risk → technical documentation, logging, human
  oversight, data governance, conformity assessment timeline (core obligations
  enforceable Aug 2026). This framework's artifacts map to those obligations.
- **US FDA**: position as non-device CDS (independent review basis = citations +
  refusal behavior) — requires counsel sign-off before pilot; the PCCP guidance
  governs any model-update process we advertise.
- **HIPAA**: de-identification gate + audit trail + BAAs for any cloud piece.
  Safe Harbor review of Presidio's redaction recall is a pre-pilot task.
