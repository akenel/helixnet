#!/bin/bash
# Keycloak Smart Entrypoint - Auto-imports realms on fresh install
# BLQ: No manual docker-compose changes needed after nuke-all
# Uses --import-realm with IGNORE_EXISTING strategy (safe for restarts)

set -e

echo "🔐 Keycloak Smart Entrypoint"
echo "   Using import strategy: IGNORE_EXISTING (safe for restarts)"

# Always use --import-realm with IGNORE_EXISTING strategy
# This is safe because Keycloak skips existing realms automatically
exec /opt/keycloak/bin/kc.sh start --optimized --import-realm "$@"
