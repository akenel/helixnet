#!/usr/bin/env bash
# ============================================================
# BorrowHood DB Backup -- Run after each episode recording
# Usage: ./scripts/bh-backup.sh <label>
# Example: ./scripts/bh-backup.sh ep01-the-crash
# ============================================================
set -euo pipefail

LABEL="${1:?Usage: bh-backup.sh <label> (e.g. ep01-the-crash)}"
DATE=$(date +%Y%m%d-%H%M)
BACKUP_DIR="/opt/helixnet/backups"
FILENAME="bh-${LABEL}-${DATE}.sql.gz"

echo "Creating backup: ${FILENAME}"
ssh root@46.62.138.218 "mkdir -p ${BACKUP_DIR} && docker exec postgres pg_dump -U helix_user borrowhood | gzip > ${BACKUP_DIR}/${FILENAME} && ls -lh ${BACKUP_DIR}/${FILENAME}"

echo ""
echo "Backup complete. To restore:"
echo "  ssh root@46.62.138.218 \"gunzip -c ${BACKUP_DIR}/${FILENAME} | docker exec -i postgres psql -U helix_user -d borrowhood\""
echo ""
echo "All backups:"
ssh root@46.62.138.218 "ls -lh ${BACKUP_DIR}/bh-*.sql.gz"
