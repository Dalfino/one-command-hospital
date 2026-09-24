# Third-party license register — v0.4.0

Commercial-grade repos know what they ship. This register covers the
components we BUILD ON (not the hospital infra images — those keep their own
licenses, noted in README's combination table).

| Component | License | Notes |
|---|---|---|
| OpenEMR (sandbox EHR) | GPL-3.0 | sandbox-only use; we invoke over API, not linking |
| Medplum | Apache-2.0 | FHIR spine |
| OpenHIM | MPL-2.0 | interop bus |
| HAPI FHIR | Apache-2.0 | conformance CI |
| Synthea | Apache-2.0 | synthetic patients |
| vLLM | Apache-2.0 | inference server |
| BioMistral-7B | Apache-2.0 | model weights (BioMistral org release) |
| Meditron corpus | guidance papers CC BY-NC where applicable | we do NOT ship Meditron weights; corpus used only as authoring reference for SYNTHETIC protocols |
| FastAPI / Starlette / Pydantic | MIT | services |
| Uvicorn | BSD-3-Clause | services |
| Presidio (analyzer/anonymizer) | MIT | de-id gate |
| spaCy | MIT | de-id NLP engine |
| en_core_web_sm model | CC BY-SA 3.0 | attributable model; swap for production |
| medspaCy | MIT | verifier ConText |
| rank-bm25 | Apache-2.0 | retrieval |
| sentence-transformers (optional) | Apache-2.0 | vector channel |
| Express | MIT | mediator |
| Caddy | Apache-2.0 | edge TLS |
| Prometheus / Grafana | Apache-2.0 / AGPL-3.0 | Grafana is AGPL — sandbox dashboards; hosted Grafana Cloud or OSS alt at production |
| Locust | MIT | load test |
| fhirclient (SMART widget) | Apache-2.0 | widget |

Review rules:
1. New dependency ⇒ add a row here in the same PR (CONTRIBUTING.md).
2. "License compatibility first" — anything copyleft that would contaminate
   distribution (not sandbox invocation) needs explicit approval.
3. Model licenses can change between versions — re-verify at each bump and
   record the hash of the weights actually deployed.
