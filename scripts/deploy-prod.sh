#!/usr/bin/env bash
# Prod deploy gate — the Dream Weavers regression (the stories) is the BLOCKING gate.
# A broken story ABORTS the prod deploy. The stories test the platform every time we ship.
#
#   scripts/deploy-prod.sh            # run the gates only (dry check — safe, no push)
#   scripts/deploy-prod.sh --deploy   # gates + push to prod (per the SOP), ONLY if green
#
# Target the gate at staging (default) or override: SQUARE=... BOTTEGA=... scripts/deploy-prod.sh
set -uo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-check}"

echo "════════════ PROD DEPLOY GATE ════════════"
echo "GATE 1 — Dream Weavers regression (the stories, vs ${SQUARE:-staging})"
if ! node tests/e2e/dream-weavers-regression.js; then
  echo ""
  echo "🔴 A STORY BROKE — prod deploy ABORTED. Fix it on staging, re-run the gate."
  exit 1
fi

echo ""
echo "GATE 2 — smoke-test (best-effort)"
if [ -f scripts/smoke-test.sh ]; then
  bash scripts/smoke-test.sh staging 2>/dev/null || echo "  ⚠️  smoke-test not green/applicable for 'staging' — regression is the hard gate, continuing"
else
  echo "  (no smoke-test.sh — skipping)"
fi

echo ""
echo "🟢 GATES GREEN — the stories all pass."
if [ "$MODE" != "--deploy" ]; then
  echo "   Dry check only. To actually push to prod:  scripts/deploy-prod.sh --deploy"
  exit 0
fi

echo "════════════ DEPLOYING TO PROD (gated behind green) ════════════"
BOX=root@46.62.138.218
ssh "$BOX" 'cd /opt/helixnet && git pull && cd hetzner && docker compose -f docker-compose.uat.yml up -d --build helix-platform borrowhood'
echo "deployed — running prod smoke…"
ssh "$BOX" 'cd /opt/helixnet && bash scripts/smoke-test.sh hetzner' || echo "⚠️  prod smoke had issues — check before announcing."
echo "✅ prod deploy complete. Write the release report: what bugs this push fixes."
