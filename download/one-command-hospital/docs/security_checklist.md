# Security Checklist — pre-production gate

> Companion to Gate 2 of `deployment_readiness.md`. Items marked ✅ are done in
> the current scaffold; ⬜ items are required before any real (even pilot) data
> touches the stack.

## 1. Identity & access

- [x] Medplum service-client auth implemented (client_credentials + JWT RS384 assertion, token cache) — `medplum-auth.js`
- [ ] **Enable it**: sandbox currently falls back to `unauthenticated-v0`; production must fail closed if `MEDPLUM_AUTH_JSON` is absent (remove the fallback path)
- [ ] Per-user SMART scope tokens; mediator records `requested_by` from a verified identity, not a client-supplied string
- [ ] OpenHIM: mutual TLS for mediator registration; console behind SSO
- [ ] Break-glass account documented, monitored, and exercised quarterly

## 2. Network

- [x] Database tier on an `internal` network (no outbound) in compose
- [x] AI services: read-only rootfs, dropped caps, no-new-privileges
- [ ] TLS termination at the edge (reverse proxy); HTTPS between OpenHIM and mediator
- [ ] Remove host-port bindings for internal services in production (access via bus / VPN only)
- [ ] Egress allow-list: AI services need NO internet at runtime (model + corpus local) — enforce and test

## 3. Data protection

- [x] Question + context de-identified before any LLM call (mediator v0.3)
- [x] Audit trail stores scrubbed question only; raw narrative never persisted
- [ ] Presidio recall audit against hospital's own PHI test set (Safe Harbor mapping, target >95% recall with over-redaction bias)
- [ ] Disk encryption for volumes (audit, DBs); key management documented
- [ ] Retention policy: Communications + audit log (recommend 6+ years per record-retention policy), model caches excluded from backups

## 4. Application hardening

- [x] Body-size caps, per-IP token-bucket rate limits on all four services
- [x] Security headers (nosniff/DENY/no-store); `x-powered-by` disabled
- [x] Zero-dependency metrics/audit modules (no supply-chain surface beyond express/presidio/fastapi)
- [ ] Dependency pinning + `pip-audit`/`npm audit` in CI (currently manual)
- [ ] Input validation review: FHIR identifiers, corpus ids, section regexes
- [ ] Error responses scrubbed (no stack traces to clients)

## 5. Secrets

- [x] No secrets in code; `.env` git-ignored; `.env.example` documents every var
- [x] CI gitleaks scan; repo history clean
- [ ] Rotate any credential that has EVER appeared in chat/tickets (including the GitHub PAT used to create this repo)
- [ ] Vault or platform secret manager for production; env-file only for sandbox

## 6. Logging & detection

- [x] Hash-chained append-only audit log + `/audit/verify` + chain-broken alert
- [x] Prometheus alerts: ungrounded answers, refusal fatigue, 5xx, service down
- [ ] Structured JSON logs with request-id propagation across the 7 hops
- [ ] Alert routing to real paging (currently dashboards only)
- [ ] Quarterly restore drill: DB volumes + audit log verify after restore

## 7. Testing

- [ ] Threat model workshop (STRIDE over the lifecycle in architecture.md)
- [ ] Third-party penetration test incl. SMART launch flow and mediator
- [ ] Fuzzing pass on `/deid`, `/answer`, `/verify`, `/process` inputs
- [ ] Negative tests: verifier down → answers marked ungrounded (exists in code; add automated test), Medplum down → answer still returned
