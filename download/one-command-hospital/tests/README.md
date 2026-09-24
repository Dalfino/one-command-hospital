# Test Suite — One-Command Hospital

Three tiers, each answering a different question before clinical sign-off.

| Tier | What it proves | Needs | Run |
|---|---|---|---|
| **unit** | Security primitives, retrieval math, cache, citation contract, eval CI gate, logging PHI policy | nothing (runs in ~2s) | `make test-unit` |
| **node** | Audit hash-chain tamper detection, log redaction, metrics exposition escaping | node ≥18 | `make test-node` |
| **integration** | The golden path over REAL containers + fail-closed + PHI white-out | docker | `make test-integration` |
| **live** | Generator behavior: trap refusals, citation validity, red-team floor | GPU stack + `RAG_URL` | `RAG_URL=http://localhost:8101 pytest tests/live -m live` |

Default `pytest` run = unit tier only (`pytest.ini` excludes integration/live).

## Integration tier

```
make test-integration          # boots tests/integration/docker-compose.test.yml
```

The test stack runs the four AI services with:

- **Mock-LLM mode** — `LLM_BASE_URL` points nowhere, so guideline-rag uses its
  honest extractive fallback (citation-prefixed, verifier-compatible). Full
  pipeline coverage with zero GPUs.
- **Deliberately unreachable Medplum** — asserts the mediator degrades
  gracefully (answer still returned, `fhir.written=false`) instead of dying.
- **Planted synthetic identifiers** ("Robert Smith", MRN 4471182…) that must
  not survive into the Communication payload (the PHI white-out test).

Scenarios covered:

1. `test_golden_path.py` — question in → de-ID → retrieval → extractive answer
   with citation → verifier grounding → audit appended → chain verifies.
2. `test_fail_closed.py` — verifier stopped mid-flight → answer returns
   **flagged for review** (`grounding=false`), never silently trusted.
3. `test_phi_leak.py` — planted identifiers detected (≥3 findings) and absent
   from every downstream surface.

## Live tier (pre-sign-off)

Runs the same safety assertions against the real BioMistral generator:
refusal traps from `eval/qa_full.yaml` (≥90% must refuse), citation validity
on answerable items (≥80%), and a red-team set that must never receive
confident cited answers.

## Bugs these tests caught (proof of value)

- **guideline-rag corpus path** (`parents[2]` → `/guidelines` in-container):
  the service would never have booted from its own compose file. Fixed with
  `GUIDELINES_DIR` env override + correct container-relative default.
- **Ungrounded answers passing silently**: an answer arriving without
  citations (extractive fallback / generator misbehavior) was marked
  `grounded=true`. Now flagged `grounded=false — answer carried no citations`.
- **Extractive fallback lost its citation header**, making mock-mode answers
  unverifiable downstream. Fallback now prepends `[CORPUS_ID §N]`.
