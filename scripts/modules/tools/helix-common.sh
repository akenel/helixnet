#!/usr/bin/env bash
# ==============================================================================
# common.sh — Shared helpers for banners, colors, gum, and safe I/O
# Part of the HelixNet Toolchain (scripts/tools/helix-common.sh)
# ==============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

# ------------------------------------------------------------------------------
# 🎨 COLORS & SYMBOLS (CI-aware + exported)
# ------------------------------------------------------------------------------
if [[ "${NO_COLOR:-false}" == "true" ]]; then
  export RED=''; export GREEN=''; export YELLOW=''; export BLUE=''; export CYAN=''; export MAGENTA=''; export NC=''
  export OK='OK'; export FAIL='FAIL'; export WARN='WARN'; export INFO='INFO'; export SKIP='SKIP'
else
  export RED='\033[0;31m'
  export GREEN='\033[0;32m'
  export YELLOW='\033[1;33m'
  export BLUE='\033[0;36m'
  export MAGENTA='\033[0;35m'
  export CYAN='\033[0;96m'
  export NC='\033[0m'
  export OK="${GREEN}✅${NC}"
  export WARN="${YELLOW}⚠️${NC}"
  export FAIL="${RED}❌${NC}"
  export INFO="${BLUE}ℹ️${NC}"
  export SKIP="${CYAN}🩺${NC}"
  
fi
export BOLD="\033[1m"
export RESET="\033[0m"

# ------------------------------------------------------------------------------
# 🧩 GUM WRAPPERS (safe fallback if gum missing)
# ------------------------------------------------------------------------------
gum_spin() {
  local secs="${1:-5s}"
  local title="${2:-Processing...}"
  if gum spin -v &>/dev/null; then
    gum spin --spinner="dot"  --title=$title --timeout=$secs 
  else
    printf "%s " "$title"
    for _ in $(seq 1 "$secs"); do printf "."; sleep 1; done
    printf "\n"
  fi
}

gum_confirm() {
  local msg="${1:-Continue?}"
  if gum spin -v &>/dev/null; then
    gum spin --spinner="dot"  --title="Continue?" --timeout=5s 
  else
    read -rp "$msg [y/N]: " ans && [[ "$ans" =~ ^[Yy]$ ]]
  fi
}

# ------------------------------------------------------------------------------
# 🧱 SAFE NETWORK + SYSTEM HELPERS
# ------------------------------------------------------------------------------
safe_curl_status() {
  local url="$1"
  curl -sk -o /dev/null -w "%{http_code}" --max-time 4 "$url" 2>/dev/null || echo "000"
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || { echo -e "${FAIL} Missing required tool: ${cmd}"; return 1; }
}

strip_ansi() { sed -r "s/\x1B\[[0-9;]*[JKmsu]//g"; }

# ------------------------------------------------------------------------------
# ☕ LITTLE CINEMA MOMENTS
# ------------------------------------------------------------------------------
time_for_tea() {
  tput civis
  for i in {1..10}; do
    tput cup 5 0
    echo "⏳ Checking containers... $(date +%T)"
    sleep 1
  done
  tput cnorm
}

# ------------------------------------------------------------------------------
# 🧠 HELIX BANNER — ASCII art + live metadata
# ------------------------------------------------------------------------------
banner_show() {
  local BANNER_FILE="$(dirname "$0")/../assets/helix-banner.txt"
  local GIT_SHA
  GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
  local CURRENT_TIME
  CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

  echo -e "${BLUE}"
  if [[ -f "$BANNER_FILE" ]]; then
    cat "$BANNER_FILE"  && echo -e "${NC}"
  else
    echo "### HELIX ###"
  fi

    printf "  ${GREEN}PROJECT:${NC} Helix AI/Ollama 🧠 | ${YELLOW}Git SHA:${NC} %s | ${YELLOW}Time:${NC} %s\n" \
    "$GIT_SHA" "$CURRENT_TIME"

  printf "  ${BLUE}OLLAMA_MODEL:${NC} %s | ${BLUE}API_URL:${NC} %s\n" \
    "${OLLAMA_MODEL:=llama3.2}" "${OLLAMA_API_URL:=http://localhost:11434}"

  local mem_total mem_used
  mem_total=$(free -g | awk '/Mem:/ {print $2}')
  mem_used=$(free -g | awk '/Mem:/ {print $3}')
  printf "  ${MAGENTA}🧠 RAM:${NC} %s GB used / %s GB total\n" "$mem_used" "$mem_total"

  echo -e "${CYAN}════════════════════════════════════════════════════════════════════════════${NC}\n"
}
