#!/usr/bin/env bash
# ---------------------------------------------------------
# 🧹 Sherlock's Docker Reset Tool v2.1
# Clean up containers, networks, volumes, and images.
# ---------------------------------------------------------
# ==========================================================
# 💥 ERROR TRAP: Catches an error and prints the line number
# ==========================================================
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
set -euo pipefail
# Set colors for output
CHECK="✔️"
# --- Emojis ---
CHECK="✅"
WARN="⚠️"
FIRE="🔥"
WAVE="💦"
WHALE="🐳"
TRASH="🗑️"
NETWORK="🌐"
BROOM="🧹"

# -----------------------------------------------------------------------------------------------
# --- 3. Colors and Emojis (Standardized) ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'; RESET='\033[0m'
OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; WARN="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
# Re-define emojis for clarity
TRASH="🗑️"; WHALE="🐳"; BROOM="🧹";
# -----------------------------------------------------------------------------------------------

# --- 1. Project Root & Configuration ---
# Locate the repository root (assuming script is in 'scripts/tools/')
# This is the most reliable way to find the root, regardless of CWD.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/env/helix.env"
# --- 2. Environment Variable Loading ---
# Load variables from the specified project .env file
if [[ -f "${ENV_FILE}" ]]; then
    echo -e "${INFO} Loading environment variables from: ${ENV_FILE}${NC}"
    # Use 'source' to load variables into the current shell
    # Use 'export' inside helix.env if variables need to be passed to subprocesses
    source "${ENV_FILE}"
else
    echo -e "${WARN} Configuration file not found: ${ENV_FILE}. Using defaults.${NC}"
fi
# Set default values if not loaded from the .env file
# Use standard shell parameter expansion: ${VAR:=default}
API_VERSION="${API_VERSION:=v2.0.1}"
HELIX_ENVIRONMENT="${HELIX_ENVIRONMENT:=local-dev}"
KEYCLOAK_DEV_REALM="${KEYCLOAK_DEV_REALM:=helixnet-dev}"

# --- 4. Print Header and Info ---
LATEST_HELIX_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "helix" | head -n 1 || true)
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
BUILD_TIME=$(date '+%Y%m%d_%H%M%S') 

echo "---"
echo -e "${WHALE} ${BOLD}Docker Reset Tool v2.1${RESET}"
echo -e "${INFO} Latest Image: ${LATEST_HELIX_IMAGE} | Git SHA: ${SHA} ${NC}"
echo -e "${INFO} Build Time: ${BUILD_TIME} ${NC}"
echo "---"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════╗"
echo "║ ${KEYCLOAK_DEV_REALM}  🔐  HELIX Full RESET ${API_VERSION}  🩺️ ${HELIX_ENVIRONMENT} ║"
echo "╚═══════> ./scripts/modules/reset_docker.sh <══════╝"
echo -e "${NC}"

# --- 5. Clipboard Helper (Unchanged but included for completeness) --
# --------------------------------------------------------------------# --- Clipboard Helper ---
# This function checks for multiple clipboard utilities in order of preference:
# 1. pbcopy (macOS)
# 2. xclip (Linux/X11)
# 3. xsel (Linux/X11)
# 4. clip.exe (Windows/WSL)
copy_to_clipboard() {
  local text="$1"

  if command -v pbcopy &>/dev/null; then
    echo -n "$text" | pbcopy
    echo -e "${GREEN}📋 Copied to clipboard (macOS)${NC}"
  elif command -v xclip &>/dev/null; then
    echo -n "$text" | xclip -selection clipboard
    echo -e "${GREEN}📋 Copied to clipboard (xclip)${NC}"
  elif command -v xsel &>/dev/null; then
    echo -n "$text" | xsel --clipboard --input
    echo -e "${GREEN}📋 Copied to clipboard (xsel)${NC}"
  elif command -v clip.exe &>/dev/null; then
    # New logic for Windows Subsystem for Linux (WSL)
    echo -n "$text" | clip.exe
    echo -e "${GREEN}📋 Copied to clipboard (Windows/WSL)${NC}"
  else
    echo -e "${YELLOW}⚠️  Clipboard not available. Please install xclip or xsel.${NC}"
  fi
}
# --- Help Menu ---
show_help() {
  cat <<EOF
${BLUE}Usage:${NC} ./reset_docker.sh [OPTIONS]

Options:
  ${YELLOW}-v, --volumes${NC}            Remove all Docker volumes (⚠️ irreversible)
  ${YELLOW}-i, --images [pattern]${NC}   Remove Docker images (optionally filter by name)
  ${YELLOW}-d, --dangling-only${NC}      Remove only dangling (<none>) images
  ${YELLOW}-h, --help${NC}               Show this help message

Examples:
  ./reset_docker.sh -v
  ./reset_docker.sh -i
  ./reset_docker.sh -i keycloak
  ./reset_docker.sh -d
EOF
  exit 0
}

# --- Utility Functions ---
confirm() {
  read -r -p "${YELLOW}${WARN} Are you sure? (y/N): ${NC}" response
  [[ "$response" =~ ^[Yy]$ ]]
}

# --- Core Cleanup Functions ---
remove_containers() {
  echo -e "\n${FIRE} Stopping and removing all containers..."
  docker ps -aq | xargs -r docker stop
  docker ps -aq | xargs -r docker rm -f
}

remove_networks() {
  echo -e "\n${NETWORK} Removing custom networks..."
  for net in $(docker network ls --quiet); do
    name=$(docker network inspect --format '{{.Name}}' "$net")
    if [[ "$name" != "bridge" && "$name" != "host" && "$name" != "none" ]]; then
      echo "  ${WAVE} Removing network ${name}"
      docker network rm "$net" || true
    fi
  done
}

remove_volumes() {
  echo -e "\n${TRASH} Removing ALL Docker volumes..."
  if confirm; then
    docker volume rm $(docker volume ls -q) 2>/dev/null || true
    echo -e "${CHECK} Volumes deleted successfully."
  else
    echo -e "${WARN} Skipped deleting volumes."
  fi
}

remove_images() {
  local pattern=${1:-}
  echo -e "\n${WHALE} Removing Docker images..."
  if [[ -n "$pattern" ]]; then
    echo -e "${BLUE}Filtering images by pattern:${NC} ${pattern}"
    docker images | grep "$pattern" | awk '{print $3}' | xargs -r docker rmi -f
  else
    if confirm; then
      docker images -a -q | xargs docker rmi -f

      # docker rmi -f $(docker images -q)
      echo -e "${CHECK} All images deleted."
    else
      echo -e "${WARN} Skipped deleting images."
    fi
  fi
}

remove_dangling_images() {
  echo -e "\n${BROOM} Cleaning up dangling (<none>) images..."
  docker images -f "dangling=true" -q | xargs -r docker rmi -f
  echo -e "${CHECK} Dangling images removed."
}

# --- Parse args ---
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
REMOVE_DANGLING=false
IMAGE_PATTERN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--volumes) REMOVE_VOLUMES=true ;;
    -i|--images) REMOVE_IMAGES=true; IMAGE_PATTERN=${2:-}; shift || true ;;
    -d|--dangling-only) REMOVE_DANGLING=true ;;
    -h|--help) show_help ;;
    *) echo -e "${RED}Unknown option:${NC} $1"; show_help ;;
  esac
  shift
done

# --- Main Logic ---
echo -e "\n${FIRE} ${BLUE}Sherlock’s Docker Reset: Cleaning your workspace...${NC}"

remove_containers
remove_networks
docker volume prune -f > /dev/null

[[ "$REMOVE_VOLUMES" == true ]] && remove_volumes
[[ "$REMOVE_IMAGES" == true ]] && remove_images "$IMAGE_PATTERN"
[[ "$REMOVE_DANGLING" == true ]] && remove_dangling_images

# Always clean dangling images silently at the end
remove_dangling_images > /dev/null 2>&1 || true

# --- Optional clipboard injection ---
copy_to_clipboard "./scripts/helix-boot.sh"

echo -e "\n${CHECK} ${GREEN}Docker environment reset complete!${NC}"
echo -e "${BLUE}You can now paste and run:${NC} ./scripts/helix-boot.sh 🚀"
echo -e "\n${CHECK} ${GREEN}Docker environment reset complete!${NC}"
echo -e "${BLUE}You can now run:${NC} ./scripts/helix-boot.sh to rebuild fresh.\n"
