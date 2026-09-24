#!/usr/bin/env bash
# backup.sh — clinical-grade backup drill (targets + hash manifest + retention).
#
# What gets backed up, and WHY:
#   guidelines/            the hospital's own protocols — the source of truth
#   eval/                  the 208-question exam + reports — the accuracy evidence
#   docs/ observe/         governance + alerting configuration as code
#   audit ledger (volume)  the tamper-evident audit trail — HIPAA §164.312(b)
#
# Every run produces one tarball + a sha256 manifest. Restore verifies the
# manifest BEFORE touching anything (tools/restore.sh). Keep last 10 locally.
#
#   make backup          (or: bash tools/backup.sh)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$REPO/backups"
ARCHIVE="$OUT/och-backup-$STAMP.tar.gz"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-one-command-hospital}"

mkdir -p "$OUT"

echo "── backup $STAMP ──────────────────────────────────────────────"
TAR_TARGETS=(guidelines eval docs observe .env.example)

# Audit ledger lives in a docker volume — pull it via a throwaway container.
if docker volume ls -q 2>/dev/null | grep -q "${COMPOSE_PROJECT}_audit-data"; then
    docker run --rm \
        -v "${COMPOSE_PROJECT}_audit-data:/src:ro" \
        -v "$OUT:/bkp" alpine \
        tar czf "/bkp/audit-$STAMP.tar.gz" -C /src . >/dev/null 2>&1 \
        && echo "audit ledger: audit-$STAMP.tar.gz" \
        || echo "WARN: audit volume read failed — is the stack running?"
else
    echo "audit volume not found (stack down?) — file-level targets only"
fi

tar czf "$ARCHIVE" -C "$REPO" "${TAR_TARGETS[@]}"
echo "repo snapshot: $(basename "$ARCHIVE") ($(du -h "$ARCHIVE" | cut -f1))"

# Hash manifest — restore refuses anything that doesn't verify.
( cd "$OUT" && sha256sum "$(basename "$ARCHIVE")" audit-"$STAMP".tar.gz 2>/dev/null \
    > "och-backup-$STAMP.sha256" || sha256sum "$(basename "$ARCHIVE")" > "och-backup-$STAMP.sha256" )
echo "manifest:      och-backup-$STAMP.sha256"

# Retention: keep the newest 10 of each artifact.
ls -1t "$OUT"/och-backup-*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm --
ls -1t "$OUT"/audit-*.tar.gz     2>/dev/null | tail -n +11 | xargs -r rm --
ls -1t "$OUT"/och-backup-*.sha256 2>/dev/null | tail -n +11 | xargs -r rm --

echo "── done. DRILL: run 'make restore FILE=backups/<name>.tar.gz' on a clean dir."
