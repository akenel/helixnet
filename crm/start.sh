#!/usr/bin/env bash
# Postino — one command to run the CRM. Creates its own venv on first run.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8900}"

if [ ! -d .venv ]; then
  echo "First run — creating virtualenv and installing dependencies..."
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

echo ""
echo "  ✉  Postino running:"
echo "     This laptop : http://localhost:${PORT}"
echo "     Your phone  : http://$(hostname -I 2>/dev/null | awk '{print $1}'):${PORT}  (same wifi)"
echo ""

# 0.0.0.0 so the Fairphone on the same wifi can reach it too
exec ./.venv/bin/uvicorn postino.main:app --host 0.0.0.0 --port "${PORT}"
