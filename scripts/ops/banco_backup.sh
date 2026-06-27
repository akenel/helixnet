#!/bin/bash
# Banco PROD nightly backup + VERIFIED RESTORE drill. 30-day retention.
# A backup you have never restored is not a backup — so every run restores the
# fresh dump into a throwaway DB and compares row counts before trusting it.
BACKUP_DIR=/opt/backups/banco
DB=banco_prod
CHECK=banco_prod_restore_check
TS=$(date +%Y%m%d_%H%M)
FILE=${BACKUP_DIR}/${DB}_${TS}.sql.gz
mkdir -p "$BACKUP_DIR"

# 1. dump + compress
docker exec postgres pg_dump -U helix_user "$DB" | gzip > "$FILE"
if [ $? -ne 0 ] || [ ! -s "$FILE" ]; then echo "[$(date)] BACKUP FAILED ($DB)" >&2; exit 1; fi
echo "[$(date)] dump OK: $(basename "$FILE") ($(du -h "$FILE" | cut -f1))"

# 2. verified restore drill (into a throwaway DB; never touches $DB)
docker exec postgres psql -U helix_user -d postgres -c "DROP DATABASE IF EXISTS ${CHECK};" >/dev/null 2>&1
docker exec postgres psql -U helix_user -d postgres -c "CREATE DATABASE ${CHECK};" >/dev/null 2>&1
gunzip -c "$FILE" | docker exec -i postgres psql -U helix_user -d "${CHECK}" >/dev/null 2>&1
Q="SELECT (SELECT count(*) FROM transactions)||'/'||(SELECT count(*) FROM products)||'/'||(SELECT count(*) FROM line_items);"
SRC=$(docker exec postgres psql -U helix_user -d "${DB}"    -tAc "$Q" 2>/dev/null)
RES=$(docker exec postgres psql -U helix_user -d "${CHECK}" -tAc "$Q" 2>/dev/null)
docker exec postgres psql -U helix_user -d postgres -c "DROP DATABASE IF EXISTS ${CHECK};" >/dev/null 2>&1
if [ -n "$SRC" ] && [ "$SRC" = "$RES" ]; then
  echo "[$(date)] RESTORE VERIFIED: txns/products/lines match ($RES)"
else
  echo "[$(date)] RESTORE MISMATCH: src=$SRC restored=$RES" >&2; exit 2
fi

# 3. retention: keep 30 days
find "$BACKUP_DIR" -name "${DB}_*.sql.gz" -mtime +30 -delete
echo "[$(date)] retention: $(ls "${BACKUP_DIR}"/${DB}_*.sql.gz 2>/dev/null | wc -l) backups on disk"
