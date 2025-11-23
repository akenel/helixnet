#!/usr/bin/env bash
# ===================================================================================
# 🥋 HelixNet Health Matrix – Platinum Compact Edition
# ===================================================================================
# Author: Angel 🧩 + Sherlock Chop
# Purpose: Fast, accurate, modular health diagnostics for Helix stack.
# Audience: Junior to Senior DevOps — easy to read, easy to extend.
# -----------------------------------------------------------------------------------

# --- ⚙️ Bash Strict Mode ---
#   e → exit on error
#   u → treat unset variables as an error
#   o pipefail → catch pipeline failures
set -euo pipefail
IFS=$'\n\t'

trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
SECONDS=0 # For runtime tracking

# -----------------------------------------------------------------------------------
# --- 🌱 Environment & Configuration ---
# -----------------------------------------------------------------------------------
ENV_FILE=".env"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
else
  # Safe defaults for first-time users or CI environments
  HELIX_ENVIRONMENT="local"
  KEYCLOAK_DEV_REALM="dev"
  OLLAMA_MODEL="llama3.2"
fi

# --- Optional flag: --no-color for CI/CD logs (disables emojis/colors) ---
NO_COLOR=false
for arg in "$@"; do
  [[ "$arg" == "--no-color" ]] && NO_COLOR=true
done

# -----------------------------------------------------------------------------------
# --- 🧩 Import Shared Modules ---
# Each module adds reusable functions and variables.
# Keep them atomic and well-named in scripts/tools/.
# -----------------------------------------------------------------------------------
TOOLS_DIR="$(dirname "$0")/tools"
 
source "${TOOLS_DIR}/helix-common.sh"  # Color defs, gum wrapper, emojis
source "${TOOLS_DIR}/helix-info.sh"    # Banner printer (banner_show)
source "${TOOLS_DIR}/helix-checks.sh"    # check_toolchain()
source "${TOOLS_DIR}/helix-utils.sh"   # small helpers (curl, strip_ansi)

# If CI mode: strip color and emoji output
if $NO_COLOR; then
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; NC=''
  OK='OK'; FAIL='FAIL'; WARN='WARN'; INFO='INFO'
fi

# -----------------------------------------------------------------------------------
# --- 🧠 Helper: HTTP Check ---
# Lightweight reachability test for service URLs
# -----------------------------------------------------------------------------------
check_http() {
  local name="$1"
  local url="$2"
  local status
  status=$(safe_curl_status "$url")

  if [[ "$status" =~ ^[23][0-9]{2}$ ]]; then
    printf "%b %-25s → %s (%s)\n" "$OK" "$name" "$url" "$status"
  else
    printf "%b %-25s → %s %b(%s)${NC}\n" "$FAIL" "$name" "$url" "${RED}" "$status"
  fi
}

# -----------------------------------------------------------------------------------
# --- 🧩 Core Service Map ---
# Add or remove URLs as your Helix stack evolves.
# -----------------------------------------------------------------------------------
declare -A SERVICES=(
  [Helix_API]="https://helix-platform.local/health/healthz"
  [Keycloak]="https://keycloak.helix.local"
  [Traefik_Dashboard]="https://traefik.helix.local/dashboard/"
  [MinIO_API]="http://127.0.0.1:9001/browser/helix-bucket"
)

# -----------------------------------------------------------------------------------
# --- 🪄 MAIN EXECUTION FLOW ---
# -----------------------------------------------------------------------------------
helix_diagnostics_main() {
  clear
  banner_show # nice ASCII + version banner

  # --- TOOLCHAIN CHECK ---
  print_header "🧰 TOOLCHAIN CHECK"
  check_toolchain

  # --- HTTP STATUS MATRIX ---
  print_header "🧱 SERVICE HEALTH (HTTP)"
  for name in "${!SERVICES[@]}"; do
    url="${SERVICES[$name]}"
    [[ "$url" =~ ^http ]] && check_http "$name" "$url"
  done

  # --- DOCKER HEALTH MATRIX ---
  print_header "🐳 DOCKER CONTAINERS"
  docker ps --all --no-trunc --format "{{.Names}}\t{{.Status}}" | \
  awk -v OK="$OK" -v WARN="$WARN" -v FAIL="$FAIL" -v GREEN="$GREEN" -v RED="$RED" -v NC="$NC" '
  {
    name=$1; status=$0; emoji=OK; color=GREEN; action="Healthy"
    if (index(status,"unhealthy")) {emoji=FAIL; color=RED; action="⚠️ Needs Attention"}
    else if (index(status,"Exited")) {emoji=WARN; color=YELLOW; action="Stopped"}
    printf "%s %s%-25s%s  %-35s  %s\n", emoji, color, name, NC, status, action
  }' | column -t

  echo -e "${CYAN}------------------------------------------------${NC}"
  echo -e "💡 Focus: Check logs for red ⚠️ services above."

  # --- SYSTEM METRICS (fast summary) ---
  print_header "🌡️ SYSTEM METRICS"
  CPU=$(top -bn1 | awk '/Cpu\(s\)/ {print $2 + $4 "%"}')
  MEM=$(free -h | awk '/Mem:/ {print $3 "/" $2}')
  UP=$(uptime -p | sed 's/up //')
  echo -e "🧠 CPU: ${YELLOW}${CPU}${NC} | 💾 RAM: ${YELLOW}${MEM}${NC} | ⏱️ Uptime: ${YELLOW}${UP}${NC}"

  # --- Educational & Quick Links ---
  print_header "💡 QUICK ACCESS"
  echo -e "📊 Grafana → https://grafana.helix.local (admin/admin)"
  echo -e "📦 MinIO   → http://localhost:9000 (minio/minio123)"
  echo -e "🧩 Docs    → coming soon"
  echo -e "------------------------------------------------------------"
  echo -e "${BLUE}🥋 Bruce Lee Mode: simplicity mastered.${NC}\n"

  # --- Summary Exit for CI/CD ---
  local HEALTH_STATUS=0
  if docker ps --format '{{.Status}}' | grep -qv 'healthy'; then
    HEALTH_STATUS=1
  fi

  echo -e "\n${GREEN}✅ Diagnostics complete in ${SECONDS}s | Exit code: ${HEALTH_STATUS}${NC}"
  exit "$HEALTH_STATUS"
}

# --- 🚀 Entry Point ---
helix_diagnostics_main "$@"
