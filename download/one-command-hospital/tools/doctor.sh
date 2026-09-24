#!/usr/bin/env bash
# make doctor — preflight check before booting the hospital.
# Verifies docker, compose, env vars, free ports, disk, GPU (optional) and
# registry reachability. Exits non-zero on any FAIL; WARNs don't block.
set -u
PASS=0; FAIL=0

ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }
warn() { echo "  WARN  $1"; }

echo "── doctor: One-Command Hospital preflight ─────────────────────"

# 1. docker + compose
if command -v docker >/dev/null 2>&1; then ok "docker present: $(docker --version | cut -d, -f1)"; else bad "docker not found"; fi
if docker compose version >/dev/null 2>&1; then ok "docker compose v2 present"; else bad "docker compose v2 missing"; fi

# 2. environment file
if [ -f .env ]; then ok ".env present"; else bad ".env missing — run: cp .env.example .env"; fi
if [ -f .env ]; then
  for v in OPENEMR_DB_ROOT_PASS OPENEMR_DB_PASS OPENEMR_ADMIN_PASS MEDPLUM_DB_PASS; do
    val=$(grep -E "^${v}=..*" .env 2>/dev/null | head -1 | cut -d= -f2-)
    if [ -n "$val" ] && ! echo "$val" | grep -q "change-me"; then ok "$v set to a real value"
    else bad "$v empty or still the template default"; fi
  done
fi

# 3. ports required by the core stack (+ observe profile)
for p in 8300 8080 8100 8101 8102 8103 8104 9000 5000 5001 8085; do
  if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${p}$"; then
    bad "port $p already in use"
  else ok "port $p free"; fi
done

# 4. disk space (images + models cache ≈ 20 GB)
free_gb=$(df -PG . 2>/dev/null | awk 'NR==2 {print int($4)}')
if [ "${free_gb:-0}" -ge 20 ]; then ok "disk free: ${free_gb} GB (≥20)"; else warn "disk free: ${free_gb} GB — model cache may not fit (recommend ≥20 GB)"; fi

# 5. GPU (only needed for make up-gpu)
if command -v nvidia-smi >/dev/null 2>&1; then
  mem=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
  if [ "${mem:-0}" -ge 24000 ]; then ok "GPU ${mem} MiB (≥24 GB for BioMistral-7B fp16)"
  else warn "GPU ${mem} MiB — below 24 GB; use a quantized build or CPU eval-only mode"; fi
else
  warn "nvidia-smi not found — GPU profile unavailable (eval-only mode still works)"
fi

# 6. registry reachability
if curl -sI --max-time 8 https://ghcr.io >/dev/null 2>&1; then ok "ghcr.io reachable"
else warn "ghcr.io unreachable — air-gapped install? Pre-pull images on a connected host."; fi

# 7. secret hygiene
if grep -rqE "github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+" --include="*.yml" --include="*.yaml" --include="*.js" --include="*.py" --include="*.md" . 2>/dev/null; then
  bad "possible token committed in tracked files — remove and rotate"
else ok "no tokens found in tracked files"; fi

echo "────────────────────────────────────────────────────────────────"
echo "doctor: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
