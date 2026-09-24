# Security Policy

## Reporting a vulnerability

This is a research build — but if you find something real, treat it as real.

- **Email**: security@willowlab.example (PGP: request key via email)
- **Do NOT** open a public GitHub issue for exploitable findings.
- Include: affected component (service + file), reproduction steps, impact
  hypothesis, and whether patient data (real or synthetic) could be affected.

**SLA (best-effort for a research project, stated for honesty):**

| Severity | First response | Fix target |
|---|---|---|
| Critical (PHI exposure, RCE, audit-tamper) | 48 h | 7 days or mitigating release |
| High (auth bypass, refusal-bypass, SSRF) | 72 h | 14 days |
| Medium/Low | 1 week | best effort, next milestone |

Coordinated disclosure: we acknowledge, confirm, fix, and credit reporters
unless they prefer anonymity. Please give us the SLA window before publishing.

## Supported versions

| Version | Support |
|---|---|
| 0.4.x (main) | active development + security fixes |
| ≤ 0.3.x | none — upgrade; audit-ledger format is backward-compatible |

## Invariants (breaking these is by definition a security bug)

1. **PHI never reaches an LLM.** deid-gate sits before every model path;
   the mediator de-identifies the question AND note context.
2. **No unflagged ungrounded answers.** Missing citations or a down verifier
   must mark the answer `grounded=false` / `pending_review` — never silently.
3. **The audit chain is append-only.** Any code path that rewrites/deletes
   `audit.jsonl` outside restore-drill tooling is critical severity.
4. **Logs carry no raw clinical narrative.** Only hashes/lengths/markers.
5. **Fail closed.** A dead component yields "flagged for review", not trust.

## Known open items (tracked in docs/security_checklist.md)

TLS with real certs + mTLS east-west (T-1/T-2), penetration test, external
secret manager, structured-log shipping off-box, per-service dependency
pinning audit, formal SBOM generation at release.
