# Edge — TLS termination (profile: `edge`)

Caddy fronts the clinical surfaces so nothing sensitive rides plaintext HTTP
to the browser:

| Route | Target | What |
|---|---|---|
| `https://localhost:8443/widget/` | `smart-app/dist` (static) | SMART on FHIR widget |
| `https://localhost:8443/api/*` | `ai-mediator:3000` | ask / signoff / audit |
| `https://localhost:8443/emr/*` | `openemr:80` | EHR pass-through (pilot convenience) |

```bash
make edge-up      # https://localhost:8443  (self-signed internal CA)
make edge-down
```

**Sandbox vs production.** The shipped `Caddyfile` uses `tls internal`
(self-signed CA generated into the `edge-data` volume) — right for pilots,
wrong for production. Going live requires:

1. A real hostname + cert strategy (ACME via the `tls <domain>` block, or
   mounted certs) — tracked as `T-1` in `docs/security_checklist.md`.
2. HSTS is already set; add mTLS between services for east-west traffic
   (currently plain inside the `hospital` network — container boundary only).
3. Extend `tests/integration` with an edge scenario: hit `:8443/api/process`
   over TLS and assert the widget loads (`/widget/` returns 200 + assets).
