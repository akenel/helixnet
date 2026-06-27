#!/bin/bash
# Banco daily smoke against SANDBOX: reset -> simulate a full two-till day ->
# verify VAT/drawer/payment reconciliation -> monkey/fuzz. Leaves a fresh
# today-dated day behind (viewable). Alerts via STATUS + FAILURES on non-zero.
LOG=/opt/banco-smoke/smoke.log
STATUS=/opt/banco-smoke/last-status.txt
FAILURES=/opt/banco-smoke/FAILURES.log
mkdir -p /opt/banco-smoke
{
  echo "================ $(date) ================"
  cd /opt/helixnet && make sandbox-reset
  python3 /opt/helix-sandbox-tree/scripts/banco_sim/banco_daily_smoke.py --env sandbox
  RC=$?
  echo "smoke exit=$RC"
  echo "$(date +'%F %T') exit=$RC" > "$STATUS"
  if [ "$RC" -ne 0 ]; then echo "$(date +'%F %T') SMOKE FAILED exit=$RC" >> "$FAILURES"; fi
} >> "$LOG" 2>&1
