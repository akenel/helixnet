#!/usr/bin/env bash
# scripts/helix-boot.sh  -- Master boot script (Style A) with --ci / --no-gum / --no-color
set -euo pipefail
IFS=$'\n\t'
SECONDS=0

# load utils
# shellcheck source=/dev/null
source "$(dirname "$0")/tools/helix-utils.sh"

# load pre-flight sys-check function (your helix-checks.sh defines check_toolchain)
# shellcheck source=/dev/null
if [[ -f "$(dirname "$0")/tools/helix-checks.sh" ]]; then
  source "$(dirname "$0")/tools/helix-checks.sh"
fi

# CLI flags
CI_FLAG=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ci|--no-gum)
      CI_FLAG=true; shift ;;
    --no-color)
      disable_colors; shift ;;
    --no-gum)
      NO_GUM=true; shift ;;
    --ci-mode)
      CI_FLAG=true; shift ;;
    -*)
      echo "Unknown flag: $1"; exit 2 ;;
    *)
      shift ;;
  esac
done

if [[ "$CI_FLAG" == "true" ]]; then
  set_ci_mode
fi

# Load .env
load_env ".env"

# Pre-flight toolchain
echo "🔎 Running pre-flight tool checks..."
if type check_toolchain >/dev/null 2>&1; then
  check_toolchain || die "Missing required tools. Fix environment and re-run."
else
  echo "⚠️ No check_toolchain function available — make sure scripts/tools/helix-checks.sh is installed."
fi

banner_show
echo -e "${BLUE}💦️ HELIX BOOT — bring up helix-llm -> helix-core -> helix-main${NC}"
# gum_spin_safe 2 "Helix boot sequence starting..."

# ensure docker available
require_docker || die "Docker daemon not running"

# ensure networksls
create_network_if_not_exists "helixnet_core"
create_network_if_not_exists "helixnet_edge"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "ℹ️  Current project folder context: DIR=$DIR used to execute LLM stage."


# ============================================================
# 🧠 Stage 1 — TRAEFIK + LLM STACK (OLLAMA / OPENWEBUI / QDRANT)
# ============================================================

echo -e "${INFO} Stage 1 of 3 ⚡ Traefik + LLM stack${NC}"

LLM_COMP="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"
TRAEFIK_COMP="${ROOT_DIR}/compose/edge-stack.yml"

# 1) Ensure Traefik is always up FIRST
if [[ -f "$TRAEFIK_COMP" ]]; then
  gum_spin_safe 1 "Starting Traefik networking..."
  docker compose -f "$TRAEFIK_COMP" up -d --remove-orphans
  wait_for_service_healthy "traefik" 120 || echo -e "${WARN} Traefik healthcheck skipped (not defined)${NC}"
fi

# 2) LLM stack boot logic
if [[ ! -f "$LLM_COMP" ]]; then
  echo -e "${WARN} LLM stack compose not found: ${LLM_COMP}${NC}"
  return 0
fi

# ---- Detect existing containers ----
is_running() {
  docker ps --format "{{.Names}}" | grep -q "^$1$"
}

is_healthy() {
  docker inspect --format '{{.State.Health.Status}}' "$1" 2>/dev/null | grep -q "healthy"
}

echo -e "${INFO} Checking existing LLM services...${NC}"

OLLAMA_EXISTS=$(is_running ollama && echo yes || echo no)
OPENWEBUI_EXISTS=$(is_running openwebui && echo yes || echo no)
QDRANT_EXISTS=$(is_running qdrant && echo yes || echo no)

OLLAMA_HEALTHY=$(is_healthy ollama && echo yes || echo no)
OPENWEBUI_HEALTHY=$(is_healthy openwebui && echo yes || echo no)
QDRANT_HEALTHY=$(is_healthy qdrant && echo yes || echo no)

# ---- If ALL THREE already healthy → SKIP build ----
if [[ "$OLLAMA_HEALTHY" == yes && "$OPENWEBUI_HEALTHY" == yes && "$QDRANT_HEALTHY" == yes ]]; then
  echo -e "${OK} LLM stack already running & healthy. Skipping build.${NC}"
  return 0
fi

# Otherwise → Start or repair the stack
echo -e "${INFO} Launching LLM stack (ollama + openwebui + qdrant)...${NC}"
gum_spin_safe 2 "Starting LLM containers..."

docker compose -f "$LLM_COMP" up -d --build --remove-orphans

# Proper health waits
wait_for_service_healthy "ollama" 600 || echo -e "${WARN} ollama not healthy yet${NC}"
wait_for_service_healthy "openwebui" 300 || echo -e "${WARN} openwebui not healthy yet${NC}"
wait_for_service_healthy "qdrant" 300 || echo -e "${WARN} qdrant not healthy yet${NC}"
echo -e "${GREEN}Inside Container Heakth Sanity >chececk 
url -sf http://ollama:11434/api/tags ${NC}"
echo -e "${BOLD}${GREEN}ℹ️ Stage 1 Complete 🎉  ${NC}"
echo -e "${BOLD}${GREEN}   LLM Container Sanity Health Checks via cURL:${NC}"
echo -e "${BLUE}   curl -sf http://ollama:11434/api/tags   ${NC}" 
echo -e "${BOLD}${GREEN}🍿️ curl -sf http://openwebui:8080          ${NC}"
echo -e "${CYAN}   curl -sf http://qdrant:6333/collections ${NC}"

# Stage 2: core infra
if [[ -x "${DIR}/helix-boot-core.sh" ]]; then
  "${DIR}/helix-boot-core.sh" || { echo "Core stage failed"; exit 1; }
else
  echo "ℹ️  helix-boot-core.sh not found or not executable; skipping core stage"
fi

# Stage 3: main app stack
if [[ -x "${DIR}/helix-boot-main.sh" ]]; then
  "${DIR}/helix-boot-main.sh" || { echo "Main stage failed"; exit 1; }
else
  echo "ℹ️  helix-boot-main.sh not found or not executable; skipping main stage"
fi

echo -e "${GREEN}🎉 HELIX BOOT COMPLETE in ${SECONDS}s${NC}"
exit 0
