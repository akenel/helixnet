#!/bin/bash
# Banco PROD nightly backup — GPG-ENCRYPTED + VERIFIED RESTORE drill. 30-day retention.
# Dumps hold customer PII, so every backup is encrypted at rest (AES256). The drill
# DECRYPTS the fresh blob, restores it into a throwaway DB, and compares row counts —
# proving the encrypted backup is both decryptable AND restorable. The key lives in
# /root/.banco-backup-key (root-only); Angel ALSO holds a copy off-box (without it the
# .gpg files are unrecoverable — that's the point once they go offsite).
#
# OFFSITE (P5): scripts/ops/banco_offsite_pull.py pulls these .gpg blobs to a second
# machine and sha256-verifies each against the box. Ciphertext offsite + key in KeePass
# = a real disaster-recovery pair (3-2-1). This script only makes the primary copy.
BACKUP_DIR=/opt/backups/banco
KEY=/root/.banco-backup-key
DB=banco_prod
CHECK=banco_prod_restore_check
TS=$(date +%Y%m%d_%H%M)
FILE=${BACKUP_DIR}/${DB}_${TS}.sql.gz.gpg
mkdir -p "$BACKUP_DIR"
[ -s "$KEY" ] || { echo "[$(date)] NO BACKUP KEY at $KEY" >&2; exit 3; }

# 1. dump -> gzip -> gpg(AES256)
docker exec postgres pg_dump -U helix_user "$DB" | gzip \
  | gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-file "$KEY" -o "$FILE"
if [ $? -ne 0 ] || [ ! -s "$FILE" ]; then echo "[$(date)] BACKUP FAILED ($DB)" >&2; exit 1; fi
echo "[$(date)] encrypted dump OK: $(basename "$FILE") ($(du -h "$FILE" | cut -f1))"

# 2. verified restore drill — decrypt -> restore -> compare -> drop
docker exec postgres psql -U helix_user -d postgres -c "DROP DATABASE IF EXISTS ${CHECK};" >/dev/null 2>&1
docker exec postgres psql -U helix_user -d postgres -c "CREATE DATABASE ${CHECK};" >/dev/null 2>&1
gpg --batch --quiet --decrypt --passphrase-file "$KEY" "$FILE" 2>/dev/null | gunzip \
  | docker exec -i postgres psql -U helix_user -d "${CHECK}" >/dev/null 2>&1
Q="SELECT (SELECT count(*) FROM transactions)||'/'||(SELECT count(*) FROM products)||'/'||(SELECT count(*) FROM line_items);"
SRC=$(docker exec postgres psql -U helix_user -d "${DB}"    -tAc "$Q" 2>/dev/null)
RES=$(docker exec postgres psql -U helix_user -d "${CHECK}" -tAc "$Q" 2>/dev/null)
docker exec postgres psql -U helix_user -d postgres -c "DROP DATABASE IF EXISTS ${CHECK};" >/dev/null 2>&1
if [ -n "$SRC" ] && [ "$SRC" = "$RES" ]; then
  echo "[$(date)] RESTORE VERIFIED (decrypt+restore): txns/products/lines match ($RES)"
else
  echo "[$(date)] RESTORE MISMATCH: src=$SRC restored=$RES" >&2; exit 2
fi

# 3. retention: keep 30 days of encrypted blobs; purge ANY leftover plaintext dumps (PII)
find "$BACKUP_DIR" -name "${DB}_*.sql.gz.gpg" -mtime +30 -delete
find "$BACKUP_DIR" -name "${DB}_*.sql.gz" ! -name "*.gpg" -delete   # never keep unencrypted
echo "[$(date)] retention: $(ls "${BACKUP_DIR}"/${DB}_*.sql.gz.gpg 2>/dev/null | wc -l) encrypted backups on disk"
