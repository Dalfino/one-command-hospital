#!/usr/bin/env bash
# native_stack.sh — run the four AI services as bare processes, no docker.
#
# Purpose: the integration tier and the load test need a LIVE stack. Where
# docker is unavailable (dev laptops, sandboxes, some air-gapped hosts), this
# script boots the same four services with the same env the test containers
# get, so `pytest tests/integration` and locust produce identical evidence.
#
# Profiles:
#   up-test   → test ports  8210-8213, mock-LLM mode (extractive fallback)
#   up-prod   → prod ports  8100-8103 (what `make loadtest` targets)
#   down      → stop everything this script started
#   status    → one health line per service
#
# Usage:
#   bash tools/native_stack.sh up-test
#   bash tools/native_stack.sh up-prod
#   bash tools/native_stack.sh down
#   bash tools/native_stack.sh status
#
# Notes:
#   - LLM is deliberately unreachable → guideline-rag's honest extractive
#     fallback (citation-prefixed answers). This is the documented mock mode.
#   - GPU mode (v0.6.2): point guideline-rag at a live generator by exporting
#     LLM_URL before up-test/up-prod, e.g.
#       LLM_URL=http://127.0.0.1:8099/v1 bash tools/native_stack.sh up-prod
#     (vLLM serving BioMistral-7B — see docs/gpu_pilot_plan.md and
#     gpu_pilot/gpu_pilot_notebook.ipynb). Unset = the documented mock mode.
#   - Medplum is deliberately unreachable → mediator's fail-closed FHIR path.
#   - PID files in /tmp/och-native-stack are also how the fail-closed
#     integration test SIGSTOPs the verifier natively.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN=/tmp/och-native-stack
PY="${PYTHON:-python3}"
LOG="$RUN/logs"
mkdir -p "$RUN" "$LOG"

wait_healthy() { # url name tries
  local url="$1" name="$2" tries="${3:-30}"
  for _ in $(seq 1 "$tries"); do
    if curl -sf -o /dev/null "$url"; then echo "  [ok] $name"; return 0; fi
    sleep 1
  done
  echo "  [FAIL] $name did not come healthy: $url" >&2
  return 1
}

start_py() { # name dir port sfx extra_env...
  local name="$1" dir="$2" port="$3" sfx="$4"; shift 4
  if [ -f "$RUN/$name$sfx.pid" ] && kill -0 "$(cat "$RUN/$name$sfx.pid")" 2>/dev/null; then
    echo "  [skip] $name$sfx already running (pid $(cat "$RUN/$name$sfx.pid"))"; return 0
  fi
  ( cd "$REPO/$dir" && exec env "$@" "$PY" -m uvicorn app.main:app \
      --host 127.0.0.1 --port "$port" \
      > "$LOG/$name$sfx.log" 2>&1 ) &
  echo $! > "$RUN/$name$sfx.pid"
}

start_node() { # name dir port sfx
  local name="$1" dir="$2" port="$3" sfx="$4"
  if [ -f "$RUN/$name$sfx.pid" ] && kill -0 "$(cat "$RUN/$name$sfx.pid")" 2>/dev/null; then
    echo "  [skip] $name$sfx already running (pid $(cat "$RUN/$name$sfx.pid"))"; return 0
  fi
  if [ ! -d "$REPO/$dir/node_modules" ]; then
    ( cd "$REPO/$dir" && npm install --omit=dev > "$LOG/npm-install.log" 2>&1 )
  fi
  ( cd "$REPO/$dir" && exec env PORT="$port" AUDIT_DIR="$RUN/audit$sfx" \
      DEID_URL="http://127.0.0.1:$((base+0))/deid" \
      RAG_URL="http://127.0.0.1:$((base+1))/answer" \
      VERIFY_URL="http://127.0.0.1:$((base+2))/verify" \
      MEDPLUM_FHIR_URL="http://localhost:9/fhir" \
      RATE_LIMIT_RPS="50" RATE_LIMIT_BURST="100" \
      node main.js > "$LOG/$name$sfx.log" 2>&1 ) &
  echo $! > "$RUN/$name$sfx.pid"
}

boot() { # base_port llm_url sfx
  local base="$1"; local llm="$2"; local sfx="${3:-}"
  echo "booting native stack (base port $base) — logs in $LOG"
  start_py deid-gate   services/deid-gate     $((base+0)) "$sfx" \
      RATE_LIMIT_RPS=50 RATE_LIMIT_BURST=100
  start_py guideline-rag services/guideline-rag $((base+1)) "$sfx" \
      GUIDELINES_DIR="$REPO/guidelines" LLM_BASE_URL="$llm" \
      VECTOR_BACKEND=bm25 RATE_LIMIT_RPS=50 RATE_LIMIT_BURST=100
  start_py verifier    services/verifier      $((base+2)) "$sfx" \
      RATE_LIMIT_RPS=50 RATE_LIMIT_BURST=100
  start_node ai-mediator services/ai-mediator $((base+3)) "$sfx"
  wait_healthy "http://127.0.0.1:$((base+0))/health" deid-gate      60
  wait_healthy "http://127.0.0.1:$((base+1))/health" guideline-rag  60
  wait_healthy "http://127.0.0.1:$((base+2))/health" verifier       60
  wait_healthy "http://127.0.0.1:$((base+3))/health" ai-mediator    30
  echo "native stack ready: deid=$((base+0)) rag=$((base+1)) verifier=$((base+2)) mediator=$((base+3))"
}

down() {
  for f in "$RUN"/*.pid; do
    [ -f "$f" ] || continue
    local pid name
    pid=$(cat "$f"); name=$(basename "$f" .pid)
    if kill -0 "$pid" 2>/dev/null; then
      kill -CONT "$pid" 2>/dev/null || true   # undo any SIGSTOP from fail-closed tests
      kill "$pid" 2>/dev/null || true
      echo "  [stopped] $name (pid $pid)"
    fi
    rm -f "$f"
  done
}

status() {
  local rc=0
  for spec in "deid-gate 8210" "guideline-rag 8211" "verifier 8212" "ai-mediator 8213" \
              "deid-gate-prod 8100" "guideline-rag-prod 8101" "verifier-prod 8102" "ai-mediator-prod 8103"; do
    set -- $spec; local name="$1" port="$2"
    if curl -sf -o /dev/null -m 2 "http://127.0.0.1:$port/health"; then
      echo "  [up]   $name :$port"
    else
      echo "  [down] $name :$port"; rc=1
    fi
  done
  return $rc
}

case "${1:-}" in
  up-test) boot 8210 "${LLM_URL:-http://localhost:1/v1}" "" ;;
  up-prod) boot 8100 "${LLM_URL:-http://localhost:1/v1}" "-prod" ;;
  down)    down ;;
  status)  status ;;
  *) echo "usage: LLM_URL=<generator-url> $0 {up-test|up-prod|down|status}"; exit 2 ;;
esac
