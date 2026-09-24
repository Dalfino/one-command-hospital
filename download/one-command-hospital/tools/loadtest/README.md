# Load test

```bash
make loadtest                    # 20 users, ramp 2/min, 2 min, vs http://localhost:8103
LOCUST_USERS=50 LOCUST_RUN_TIME=5m make loadtest
```

Reads like ward traffic: 70% repeat questions (cache path), 20% unique
phrasings (retrieval+generate), 10% ops probes.

## SLO gates (kill-criteria aligned — docs/deployment_readiness.md)

| Metric | Target | Rationale |
|---|---|---|
| p50 `/process` | < 2000 ms (mock) | clinician patience in-chart |
| p95 `/process` | < 8000 ms | **kill criteria**: median >8s sustained ⇒ project dies |
| error rate | < 1% (excl. 429) | a copilot that errors is worse than absent |
| 429 rate | observed, tuned | rate limits protect the corpus under storm |

Procedure for a pilot sign-off:

1. `make up` (mock mode) → `make loadtest` → record p50/p95/errors in the
   readiness doc (Gate 5 evidence).
2. `make up-gpu` (live BioMistral) → repeat → compare; the live numbers are
   the ones that count for Gate 5.
3. Snapshot Prometheus during the run (`make observe`) — refusal-fatigue and
   ungrounded counters must stay flat while latency climbs.

## No-docker note

`make loadtest` prefers a locally-installed locust (`pip install locust`) and
falls back to the docker image. When docker is unavailable, boot the target
stack with `make stack-prod` (bare-process, ports 8100-8103) first — see
`tools/native_stack.sh`. Same scenarios, same SLO gates.
