#!/bin/bash
# ================================================================
# Keycloak Migration Runner
#
# Executes numbered migration scripts via kcadm.sh (inside the
# Keycloak container). Tracks applied migrations in .applied file.
# Each migration is idempotent -- safe to run twice.
#
# Usage:
#   Local:    bash scripts/kc-migrations/migrate.sh
#   Hetzner:  ssh root@46.62.138.218 "cd /opt/helixnet && bash scripts/kc-migrations/migrate.sh"
#
# Environment variables (all have defaults):
#   KC_CONTAINER  - Docker container name (default: keycloak)
#   KC_ADMIN_USER - Admin username (default: helix_user)
#   KC_ADMIN_PASS - Admin password (default: helix_pass)
# ================================================================

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="${SCRIPT_DIR}/migrations"
APPLIED_FILE="${SCRIPT_DIR}/.applied"

KC_CONTAINER="${KC_CONTAINER:-keycloak}"
KC_ADMIN_USER="${KC_ADMIN_USER:-helix_user}"
KC_ADMIN_PASS="${KC_ADMIN_PASS:-helix_pass}"

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "================================================"
echo "  Keycloak Migration Runner"
echo "  Container: ${KC_CONTAINER}"
echo "================================================"
echo ""

# --- Pre-flight: Check container is running ---
if ! docker ps --format '{{.Names}}' | grep -q "^${KC_CONTAINER}$"; then
    echo -e "${RED}ERROR: Container '${KC_CONTAINER}' is not running.${NC}"
    exit 1
fi

# --- Pre-flight: Authenticate kcadm.sh ---
echo "Authenticating with Keycloak admin API..."
if ! docker exec "${KC_CONTAINER}" /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "${KC_ADMIN_USER}" \
    --password "${KC_ADMIN_PASS}" 2>/dev/null; then
    echo -e "${RED}ERROR: Failed to authenticate with Keycloak.${NC}"
    exit 1
fi
echo -e "${GREEN}Authenticated.${NC}"
echo ""

# --- Create applied file if it doesn't exist ---
touch "${APPLIED_FILE}"

# --- Find and run pending migrations ---
PENDING=0
APPLIED=0

for migration in "${MIGRATIONS_DIR}"/*.sh; do
    [ -f "$migration" ] || continue

    filename=$(basename "$migration")

    # Skip if already applied
    if grep -qxF "$filename" "${APPLIED_FILE}" 2>/dev/null; then
        echo -e "  ${CYAN}[SKIP]${NC} ${filename} (already applied)"
        continue
    fi

    PENDING=$((PENDING + 1))
    echo -e "  ${YELLOW}[RUN]${NC}  ${filename}"

    # Execute the migration, passing env vars
    if KC_CONTAINER="${KC_CONTAINER}" bash "$migration"; then
        echo "$filename" >> "${APPLIED_FILE}"
        echo -e "  ${GREEN}[OK]${NC}   ${filename}"
        APPLIED=$((APPLIED + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} ${filename}"
        echo -e "${RED}Migration failed. Stopping.${NC}"
        exit 1
    fi

    echo ""
done

# --- Summary ---
TOTAL=$(wc -l < "${APPLIED_FILE}" | tr -d ' ')
echo "================================================"
echo "  Results: ${APPLIED} applied, ${TOTAL} total"
echo "================================================"
echo ""

if [ $PENDING -eq 0 ]; then
    echo -e "${GREEN}All migrations already applied. Nothing to do.${NC}"
fi
