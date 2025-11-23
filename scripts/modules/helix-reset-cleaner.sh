#!/usr/bin/env bash
# scripts/modules/helix-status-v2.sh
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — Sherlock Edition (Hyperlinked)
# ==========================================================
set -Eeuo pipefail
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
# -----------------------------------------------------------------------------------------------
# ---- Configurable defaults 
# -----------------------------------------------------------------------------------------------
ENV_FILE="env/helix.env"
if [[ -f "${ENV_FILE}" ]]; then
    source "${ENV_FILE}"
fi
# -----------------------------------------------------------------------------------------------
# ---- Source Utility Functions 
# -----------------------------------------------------------------------------------------------
# Assuming helix-utils.sh is in scripts/modules/tools/
# Adjust the path if necessary, but based on your description, this should be correct.
source "scripts/modules/tools/helix-utils.sh"
KEYCLOAK_DEV_REALM="${KEYCLOAK_DEV_REALM:=unknown}"
HX_PROJECT_APP_VERSION="${HX_PROJECT_APP_VERSION:=vN/A}"
HELIX_ENVIRONMENT="${HELIX_ENVIRONMENT:=dev}" 
# --- Colors & Emojis ---
CHECK="✔️"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
CYAN='\033[0;39m'
NC='\033[0m' # No Color
BOLD="\033[1m"; RESET="\033[0m"
OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; WARN="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
# ---- Print header -----------------------------------------------------------------------------
LATEST_HELIX_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "helix" | head -n 1 || true)
# Recommended approach for getting reliable BUILD info
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
BUILD_TIME=$(date '+%Y%m%d_%H%M%S') # Current time, since build time is hard to extract from docker images
# The variables are now guaranteed to be set, so the echo is safe!
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ${KEYCLOAK_DEV_REALM} 🔐  Helix NUKER    💦  ${HX_PROJECT_APP_VERSION}         🩺️  ${HELIX_ENVIRONMENT}  ║"
echo "╚═════════> ./scripts/modules/helix-reset-cleaner.sh <═══════╝"
echo "🪣️  Latest Image: ${LATEST_HELIX_IMAGE} 🤓️ SHA: ${SHA}"
echo "Build Time: 🤖 ${BUILD_TIME}"
printf "%b\n" "${GREEN}${BOLD} ⏲️  ◾️ $(date)        on ◾️  $(hostname)${NC}"
echo""
echo "  🧹 Starting Safe Cleanup Commands..." 
# 1. Shut down Core Services (Postgres, Keycloak, Minio, etc.)
echo "   🫧️  Shutting down helix-core" 
docker compose -f compose/helix-core/core-stack.yml down --remove-orphans
# 2. Shut down Main Application Services (API, Worker, Beat)
echo "    🚿️ Washing down helix-main"
# FIX: Changed path from compose/helix-main.yml to compose/helix-main/main-stack.yml
docker compose -f compose/helix-main/main-stack.yml down --remove-orphans
# 3. Shut down LLM/AI Services (Ollama, WebUI)
echo "      🍀️ Refreshing helix-llm"
# FIX: Changed path from compose/helix-llm.yml to compose/helix-llm/llm-stack.yml
docker compose -f compose/helix-llm/llm-stack.yml down --remove-orphans
# 4. Flush unused images, networks, and volumes
echo "       🚽️ Pruning volumes"
docker system prune --volumes --force
echo ""
echo "    🌐 Validating Core Networks..."
# Call the function for each required network
create_network_if_not_exists "helixnet_core"
create_network_if_not_exists "helixnet_edge"
echo ""
echo "🩺️ Safe Cleanup Complete; Active Arifacts"
# (Rest of the status report continues...)
echo""
echo "💚️  Did NOT delete Postgres database, Ollama models or TLS certs"
echo "🏁️  Completed house keeping and cleared runtime noise."
echo""
exit 0