# PROJECT STATE — One-Command Hospital

> **THIS FILE IS THE SESSION ANCHOR.** The dev sandbox is ephemeral: its
> filesystem is wiped on resets and nothing survives unless it is committed
> and pushed to GitHub. Any agent (or human) starting a new session MUST:
>
> 1. `git clone https://github.com/Dalfino/one-command-hospital.git` (if the
>    workspace is empty) — the workspace repo root is one level above this
>    file's parent (`/home/z/my-project`), which also carries the portal app.
> 2. Read this file top-to-bottom.
> 3. Read `worklog.md` (repo root, multi-agent log) — last 2 entries minimum.
> 4. Read `CHANGELOG.md` for the milestone ledger detail.
> 5. Then, and only then, start new work.
>
> **End-of-session protocol (mandatory):** commit everything (minus secrets)
> and `git push origin main`. A session that ends without a push lost its work.

- **Repo:** https://github.com/Dalfino/one-command-hospital (PRIVATE since 2026-09-24)
- **Version:** v0.6.0 (M19–M23 safety+governance wave + tech radar)
- **Status:** high-fidelity prototype on synthetic data; Gate 0–5 evidence
  produced in mock/simulated mode; NOT clinically deployable (see Blockers).

---

## Why the sandbox "keeps losing things"

The sandbox is a container with an ephemeral root filesystem. Between sessions
the following are wiped: git remotes (stored in `.git/config`), generated
`.env`, pip installs, running processes, anything in `/tmp`. What survives is
only what was **committed and pushed**. Rules that make iterations cheap:

1. **GitHub is the source of truth.** Local history was force-pushed over the
   stale M0–M6 remote history on 2026-09-24 (old remote HEAD was `09b92ec`,
   preserved here for forensics). Never assume the remote is behind — push.
2. **STATE.md + worklog.md + CHANGELOG.md are the context.** They travel with
   the repo. Reading them reconstructs full project memory in any fresh session.
3. **PAT policy: inline-only.** The fine-grained PAT is pasted in chat when
   needed, used for the single push/API call, and never written to any file
   git can see (`.git/config` remote URL does not survive resets anyway).
   Rotate the PAT if it ever appears in a log or file. Secret scan before
   every push: `grep -rqE "github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+" --exclude-dir=node_modules .`
4. **Rebuild is scripted, not remembered.** A fresh host goes zero → running
   with `make bootstrap` (docker path) or `make bootstrap-native` (no docker).
   Nothing about environment setup lives in anyone's head.

## Architecture map (what lives where)

```
download/one-command-hospital/
├── services/            4 AI services, all containerized (own Dockerfile)
│   ├── deid-gate/       :8100  Presidio PHI scrubbing (Python/FastAPI)
│   ├── guideline-rag/   :8101  BM25(+SBERT) RAG over guidelines (Python)
│   ├── verifier/        :8102  grounding/citation verification (Python)
│   └── ai-mediator/     :8103  orchestrator + audit chain (Node 20)
├── docker-compose.yml   full stack: OpenEMR, Medplum(+pg/redis), OpenHIM,
│                        AI services, profiles: gpu/observe/edge/conformance/patients
├── tests/               unit(py) · node(node:test) · integration(py,docker-or-native) · live(py,GPU-gated)
├── eval/                qa_seed.yaml(42) · qa_full.yaml(208) · run_eval.py · evidence/
├── tools/               doctor.sh · native_stack.sh · bootstrap.sh · backup/restore.sh · loadtest/
├── docs/                deployment_readiness.md(Gates 0–5) · governance.md · model_card.md · api/openapi.yaml
├── portal/              willow portal app copy (workspace twin: /home/z/my-project/src)
├── smart-app/           SMART-on-FHIR widget (dist/ built)
├── edge/                Caddy TLS terminator config
└── observe/             Prometheus rules + Grafana provisioning
```

Port map: 8100 de-id · 8101 RAG · 8102 verifier · 8103 mediator · 8104 vLLM
(gpu profile) · 8105 HAPI · 8106 Prometheus · 8107 Grafana · 8300 OpenEMR ·
8443 edge TLS. Native test stack uses 8210–8213; prod-shape native 8100–8103.

## Milestone ledger (detail in CHANGELOG.md)

| M | Delivered |
|---|---|
| M0–M6 | 4 services, compose stack, seed eval, FHIR/SMART integration, audit v1 |
| M7–M11 (0875c1f) | network segmentation, read-only rootfs + cap_drop, rate limits, hash-chained audit + /audit/verify, governance/model-card/security docs, Prometheus+Grafana+alerts, 208-question eval (95%), doctor.sh, CI, answer cache, ambiguity margin |
| M12–M16 (9a12a2c, v0.4.0) | test pyramid (unit/node/integration/live), trace-id propagation, JSON redacting logs, TLS edge, verified backup/restore, locust SLO harness, LICENSE/CHANGELOG/CONTRIBUTING/SECURITY/OpenAPI/SBOM, 4 real bugs fixed by tests |
| M17 (db0d519, v0.5.0) | **live Gate 5 evidence**: integration 10/10 vs running stack, load 0 errors (p95 31ms @50u), 4 real bugs fixed (citation-text verifier contract, upstream timeouts, 7-digit phone PHI recall, Presidio cold-boot model), docker-optional native test path |
| M18 (b19cebf, v0.5.1) | repo pushed to private GitHub as source of truth; STATE.md anchor; make bootstrap[-native]; .dockerignore ×5; Gate 5 re-verified after full environment reset |
| M19–M23 (v0.6.0) | injection guard (8/8 live refusals) · calibration (ECE/risk-coverage/threshold) · sense-consistency verifier (historical/family) · clinician review queue + feedback→eval loop (live E2E verified) · claim-level faithfulness (0.94 first measurement) · docs/tech_radar.md |

## Gate status (deployment_readiness.md is the authoritative matrix)

| Gate | Meaning | State |
|---|---|---|
| 0 | Repo hygiene, license, docs | ✅ |
| 1 | Unit + node tests | ✅ 37/37 + 17/17 |
| 2 | Eval gates (seed + full) | ✅ 98% / 95% (mock-mode generator) |
| 3 | Integration tier (golden path, fail-closed, PHI white-out) | ✅ 10/10 vs live stack |
| 4 | Security/ops artifacts (TLS edge, backup, SBOM, CI, alerts) | ✅ artifacts done; real-cert TLS + pen test pending |
| 5 | Load/SLO evidence | ✅ mock-mode: 0 errors, p95 31ms @50u, 15.4 req/s; **GPU-stack re-run = final sign-off** |

## Six-dimension gap ledger (commercial + clinical-ready)

**Security** — done: compose segmentation (internal `data` net), non-root +
cap_drop + read-only rootfs + no-new-privileges, per-IP token-bucket rate
limits, body caps, security headers, secret-hygiene in doctor/CI, TLS edge
(sandbox internal CA). **Open:** real certs + external pen test, KMS/secret
manager integration, immutable off-box audit shipping, OIDC/SSO for clinician
UI, production rate-limit tuning.

**AI Governance** — done: model card, hash-chained append-only audit with
verify endpoint + alerts, answer events carry recall/verification decisions,
kill criteria documented, change-control classes. **Open:** clinician review
queue UI workflow, human-feedback loop wired into eval set, model version
pinning in registry, EU-AI-Act/FDA counsel sign-off.

**Accuracy** — done: 208-question gated eval (95%), trap taxonomy, refusal
discipline tests (live tier written), ambiguity margin gate, retrieval
threshold gates. **Open:** GPU live-mode eval run (trap refusal ≥90%,
citation validity ≥80% — extractive mock records xfail), confidence
calibration, ConText negation/temporality in verifier, eval set expansion
with clinician-validated items.

**Infrastructure** — done: healthchecks + service_healthy gating, structured
redacting JSON logs, request/trace-id propagation, CI (eval+unit+node+compose+
gitleaks+integration job), verified backup/restore scripts, doctor preflight,
bootstrap for fresh hosts. **Open:** off-box log shipping, backup drill on
deployed stack, multi-AZ/HA story, image signing.

**Efficiency** — done: TTL+LRU answer cache, vLLM prefix caching, verifier NLP
built once, locust load harness with SLO gates. **Open:** load test on GPU
stack (mock-mode numbers are not clinical numbers), saturation/soak runs,
autoscaling policy.

**Smoothness (testing)** — done: one-command `make` targets for every tier
(`test-unit/test-node/test-integration[-native]/loadtest/eval[-full]/doctor/
backup/restore/audit-verify`), native docker-optional path, evidence files in
eval/evidence/. **Open:** `make bootstrap` on the real GPU host, UAT script
for clinician walkthrough, demo dataset load story.

## Remaining blockers to clinical-ready (the honest list)

> Full bar-by-bar assessment + prioritized upgrade roadmap (P0 buildable /
> P1 GPU-host / P2 organizational) lives in **`docs/world_class_bar.md`** —
> read that before planning any new work wave.

1. Real clinical guideline corpus + clinical steward sign-off (content is
   synthetic/placeholder — this is the #1 blocker and is a human task).
2. GPU-stack live-mode run: `LIVE_MODE=gpu make -C tests/live ...` strict gates
   + rerun eval + loadtest against vLLM (Gate 5 final sign-off).
3. TLS with real certs + external penetration test.
4. Medplum auth fail-closed wiring for production FHIR (mocked in tests).
5. Backup/restore drill EXECUTED on the deployed stack.
6. Regulatory counsel + governance committee ratification.

## Key commands

```bash
make doctor                     # preflight: docker/env/ports/disk/gpu/secrets
make bootstrap                  # fresh host → running stack (docker path)
make bootstrap-native           # fresh host → running stack (no docker)
make up / up-gpu / observe      # stack variants
make test-unit && make test-node
make test-integration           # docker test stack; -native if no docker
make loadtest LOCUST_USERS=50 LOCUST_RUN_TIME=2m
make eval && make eval-full
make audit-verify && make backup && make restore FILE=backups/<name>.tar.gz
```
