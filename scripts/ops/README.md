# Banco ops scripts (deployed on the Hetzner box)

Infrastructure-as-code copies of the cron'd jobs. The live copies are at
`/opt/backups/banco_backup.sh` and `/opt/banco-smoke_run.sh` on root@46.62.138.218.

| Cron (UTC) | Where | Script | Does |
|------------|-------|--------|------|
| `0 3 * * *`  | box | `banco_backup.sh` | pg_dump `banco_prod` → gzip → **GPG AES256** (key `/root/.banco-backup-key`), **verified restore** (decrypt→restore→compare row counts) into a throwaway DB, 30-day retention. Logs to `/opt/backups/banco/backup.log`. |
| `30 3 * * *` | box | `banco_smoke_run.sh` | `make sandbox-reset` → `banco_daily_smoke.py --env sandbox` (full-day sim + VAT/drawer reconciliation + monkey/fuzz). Status → `/opt/banco-smoke/last-status.txt`, failures → `/opt/banco-smoke/FAILURES.log`. |
| `@hourly` | laptop | `banco_offsite_pull.py` | **P5 offsite** — scp the encrypted `.gpg` blobs box→laptop (`~/backups/banco-offsite/`), sha256-verify newest 3 bit-identical to the box, **then `rclone copy` → Google Drive** (`ecolution-gdrive:HelixNet-DB-Backups/banco`) + `rclone check` (MD5) to verify the cloud copy. 90-day retention both places. Idempotent. Cloud push is **copy + age-delete, never `rclone sync`** (a laptop wipe can't cascade-delete the cloud copy). Status → `STATUS.txt`, log → `offsite-pull.log`. `--no-cloud` skips Drive; append remotes to `DEFAULT_REMOTES` (e.g. DigitalOcean Spaces) for provider-diversity. |

**Backups now live in 3 places: box + laptop + Google Drive** (the same Drive as the KeePass kdbx + DR SOP — one DR place). Freshness of the Drive copy depends on the laptop being on (it's the relay); the box keeps all 30 days regardless. A future box→Drive-direct push would make it 24/7 but puts a Google token on the server — deferred.

**Offsite = ciphertext + KEY in KeePass.** The blobs are AES256 ciphertext, ONLY recoverable with the backup key (`/root/.banco-backup-key`, fingerprint sha256[:16] = `4de994a0ef02fd82`). That key MUST live off-box too — it belongs in the KeePass kdbx that's already on Drive. Ciphertext on Drive + key in kdbx on Drive = defense-in-depth (the kdbx is master-password-encrypted). For true separation, keep the key somewhere other than Drive.

To update a live box job: edit here, then scp to the box path and re-run once to validate.
Alerting today = status/FAILURES files (pull). TODO: push (Telegram bot / email) on non-zero.
