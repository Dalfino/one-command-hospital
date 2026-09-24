#!/usr/bin/env bash
# bootstrap.sh — fresh host, zero to running stack.
#
#   bash tools/bootstrap.sh              # docker path (default)
#   bash tools/bootstrap.sh --gpu        # + vLLM profile (needs NVIDIA GPU)
#   bash tools/bootstrap.sh --observe    # + Prometheus/Grafana
#   bash tools/bootstrap.sh --edge       # + TLS terminator :8443
#   bash tools/bootstrap.sh --native     # no docker: bare-process prod stack
#   bash tools/bootstrap.sh --down       # stop whatever this script started
#
# Idempotent: safe to re-run. Generates .env with fresh random passwords on
# first run (never overwrites an existing .env), then brings the stack up and
# waits for all four AI services to report healthy before returning.
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="docker"; WITH_GPU=0; WITH_OBSERVE=0; WITH_EDGE=0; ACTION="up"
for arg in "$@"; do
  case "$arg" in
    --gpu)     WITH_GPU=1 ;;
    --observe) WITH_OBSERVE=1 ;;
    --edge)    WITH_EDGE=1 ;;
    --native)  MODE="native" ;;
    --down)    ACTION="down" ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown flag: $arg (see --help)"; exit 2 ;;
  esac
done

# ── 1. .env: create with random secrets if absent (never overwrite) ──────────
if [ ! -f .env ]; then
  echo "[bootstrap] no .env — generating one with random passwords"
  {
    echo "OPENEMR_DB_ROOT_PASS=$(openssl rand -hex 16 2>/dev/null || head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    echo "OPENEMR_DB_PASS=$(openssl rand -hex 16)"
    echo "OPENEMR_ADMIN_USER=admin"
    echo "OPENEMR_ADMIN_PASS=$(openssl rand -hex 12)"
    echo "MEDPLUM_DB_PASS=$(openssl rand -hex 16)"
    echo "MEDPLUM_AUTH_JSON="   # production: {"clientId":...,"clientSecret":...}
    echo "HAPI_DB_PASS=$(openssl rand -hex 16)"
    echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 12)"
    echo "SYNTHEA_POPULATION=100"
    echo "HF_TOKEN="
    echo "LLM_MODEL=BioMistral/BioMistral-7B"
  } > .env
  echo "[bootstrap] wrote .env (gitignored) — keep a copy of the passwords somewhere safe"
else
  echo "[bootstrap] .env present — keeping existing secrets"
fi

if [ "$ACTION" = "down" ]; then
  if [ "$MODE" = "native" ]; then bash tools/native_stack.sh down
  else docker compose --profile gpu --profile observe --profile edge down; fi
  echo "[bootstrap] stack down"; exit 0
fi

# ── 2. Bring the stack up ────────────────────────────────────────────────────
if [ "$MODE" = "native" ]; then
  if command -v docker >/dev/null 2>&1; then
    echo "[bootstrap] note: docker IS available — native mode chosen explicitly"
  else
    echo "[bootstrap] docker not found — using the native (bare-process) path"
  fi
  bash tools/native_stack.sh up-prod
else
  command -v docker >/dev/null 2>&1 || {
    echo "ERROR: docker not found. Install docker + compose plugin, or re-run with --native." >&2; exit 1; }
  docker compose version >/dev/null 2>&1 || {
    echo "ERROR: docker compose plugin missing. See https://docs.docker.com/compose/install/" >&2; exit 1; }
  PROFILES=""
  [ "$WITH_GPU" = "1" ]     && PROFILES="$PROFILES --profile gpu"
  [ "$WITH_OBSERVE" = "1" ] && PROFILES="$PROFILES --profile observe"
  [ "$WITH_EDGE" = "1" ]    && PROFILES="$PROFILES --profile edge"
  # shellcheck disable=SC2086
  docker compose $PROFILES up -d --build
fi

# ── 3. Wait for the four AI services to be healthy ──────────────────────────
echo "[bootstrap] waiting for AI services (deid 8100 / rag 8101 / verifier 8102 / mediator 8103)"
ok=0
for i in $(seq 1 60); do
  ok=1
  for p in 8100 8101 8102 8103; do
    curl -sf -o /dev/null --max-time 2 "http://localhost:$p/health" || { ok=0; break; }
  done
  [ "$ok" = "1" ] && break
  sleep 2
done
if [ "$ok" = "1" ]; then
  echo "[bootstrap] ALL FOUR SERVICES HEALTHY"
  echo "  mediator API : http://localhost:8103  (POST /process)"
  echo "  audit verify : http://localhost:8103/audit/verify"
  echo "  next steps   : make doctor && make eval && make test-integration"
else
  echo "WARNING: services not all healthy after 120s — check 'make logs' (docker) or tools/native_stack.sh status" >&2
  exit 1
fi
