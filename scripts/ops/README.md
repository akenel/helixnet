# Banco ops scripts (deployed on the Hetzner box)

Infrastructure-as-code copies of the cron'd jobs. The live copies are at
`/opt/backups/banco_backup.sh` and `/opt/banco-smoke_run.sh` on root@46.62.138.218.

| Cron (UTC) | Script | Does |
|------------|--------|------|
| `0 3 * * *`  | `banco_backup.sh` | pg_dump `banco_prod` → gzip, **verified restore** into a throwaway DB (compares row counts), 30-day retention. Logs to `/opt/backups/banco/backup.log`. |
| `30 3 * * *` | `banco_smoke_run.sh` | `make sandbox-reset` → `banco_daily_smoke.py --env sandbox` (full-day sim + VAT/drawer reconciliation + monkey/fuzz). Status → `/opt/banco-smoke/last-status.txt`, failures → `/opt/banco-smoke/FAILURES.log`. |

To update a live job: edit here, then scp to the box path and re-run once to validate.
Alerting today = status/FAILURES files (pull). TODO: push (Telegram bot / email) on non-zero.
