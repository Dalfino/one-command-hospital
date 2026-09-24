#!/usr/bin/env bash
# restore.sh — verified restore drill. Verifies the sha256 manifest FIRST,
# then restores. A backup you haven't restored is a rumor, not a backup.
#
#   bash tools/restore.sh backups/och-backup-YYYYmmdd-HHMMSS.tar.gz [--with-audit]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="${1:?usage: restore.sh backups/och-backup-<stamp>.tar.gz [--with-audit]}"
WITH_AUDIT="${2:-}"
STAMP="$(basename "$ARCHIVE" | sed 's/och-backup-//; s/\.tar\.gz//')"
MANIFEST="$REPO/backups/och-backup-$STAMP.sha256"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-one-command-hospital}"

[ -f "$ARCHIVE" ] || { echo "archive not found: $ARCHIVE"; exit 1; }
[ -f "$MANIFEST" ] || { echo "manifest not found: $MANIFEST (refusing to restore unverified)"; exit 1; }

echo "── verify ─────────────────────────────────────────────────────"
if grep -q "audit-$STAMP.tar.gz" "$MANIFEST"; then
    ( cd "$REPO/backups" && sha256sum -c "och-backup-$STAMP.sha256" )
else
    ( cd "$REPO/backups" && sha256sum -c "och-backup-$STAMP.sha256" 2>/dev/null || \
      sha256sum -c <(grep -v audit "$MANIFEST") )
fi

echo "── restore repo snapshot ──────────────────────────────────────"
tar xzf "$ARCHIVE" -C "$REPO"
echo "restored: guidelines/ eval/ docs/ observe/ .env.example → $REPO"

if [ "$WITH_AUDIT" = "--with-audit" ]; then
    AUDIT_TGZ="$REPO/backups/audit-$STAMP.tar.gz"
    if [ -f "$AUDIT_TGZ" ]; then
        echo "── restore audit ledger into volume ───────────────────────"
        docker run --rm \
            -v "${COMPOSE_PROJECT}_audit-data:/dst" \
            -v "$REPO/backups:/src:ro" alpine \
            sh -c "cd /dst && rm -rf ./audit.jsonl && tar xzf /src/audit-$STAMP.tar.gz -C /dst"
        echo "audit ledger restored. Run 'make audit-verify' to confirm the chain."
    else
        echo "no audit archive for $STAMP — ledger not restored"
    fi
fi

echo "── done. Next: 'make up' and run the eval gate before serving traffic."
