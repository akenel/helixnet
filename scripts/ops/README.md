# Banco ops scripts (deployed on the Hetzner box)

Infrastructure-as-code copies of the cron'd jobs. The live copies are at
`/opt/backups/banco_backup.sh` and `/opt/banco-smoke_run.sh` on root@46.62.138.218.

| Cron (UTC) | Where | Script | Does |
|------------|-------|--------|------|
| `0 3 * * *`  | box | `banco_backup.sh` | pg_dump `banco_prod` → gzip → **GPG AES256** (key `/root/.banco-backup-key`), **verified restore** (decrypt→restore→compare row counts) into a throwaway DB, 30-day retention. Logs to `/opt/backups/banco/backup.log`. |
| `30 3 * * *` | box | `banco_smoke_run.sh` | `make sandbox-reset` → `banco_daily_smoke.py --env sandbox` (full-day sim + VAT/drawer reconciliation + monkey/fuzz). Status → `/opt/banco-smoke/last-status.txt`, failures → `/opt/banco-smoke/FAILURES.log`. |
| `@hourly` | laptop | `banco_offsite_pull.py` | **P5 offsite** — scp the encrypted `.gpg` blobs box→laptop (`~/backups/banco-offsite/`), sha256-verify the newest 3 are bit-identical to the box, 90-day local retention. Idempotent (skips blobs already held at matching size). Status → `STATUS.txt`, log → `offsite-pull.log`. |

**Offsite = ciphertext here + KEY in KeePass.** The pulled blobs are AES256 ciphertext; they are ONLY recoverable with the backup key (`/root/.banco-backup-key`, fingerprint sha256[:16] = `4de994a0ef02fd82`). That key MUST live off-box too (Angel's KeePass) or the offsite copy is unrecoverable. The laptop pull is an opportunistic secondary (fires only when the laptop is on); the durable always-on offsite (Hetzner Storage Box push, or Backblaze B2) is a pending decision — see worklist P5.

To update a live box job: edit here, then scp to the box path and re-run once to validate.
Alerting today = status/FAILURES files (pull). TODO: push (Telegram bot / email) on non-zero.
