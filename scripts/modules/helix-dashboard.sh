#!/usr/bin/env bash
# scripts/modules/helix-dashboard.sh
# =============================================================
# 🧠 HelixNet Live Control Matrix – TUI Edition (Bruce Lee Mode)
# - Self-contained script to provide real-time status.
# =============================================================

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail
# Set IFS to only space, tab, and newline for safer word splitting
IFS=$'\n\t'

# --- 1. COLOR & SYMBOL DEFINITIONS (Self-Contained) ---
# Check if TTY is present to decide on color use
if [[ -t 1 && ! -n "${NO_COLOR:-}" ]]; then
  RED=$(tput setaf 1 2>/dev/null || echo '\033[31m')
  GREEN=$(tput setaf 2 2>/dev/null || echo '\033[32m')
  YELLOW=$(tput setaf 3 2>/dev/null || echo '\033[33m')
  BLUE=$(tput setaf 4 2>/dev/null || echo '\033[34m')
  CYAN=$(tput setaf 6 2>/dev/null || echo '\033[36m')
  BOLD=$(tput bold 2>/dev/null || echo '\033[1m')
  NC=$(tput sgr0 2>/dev/null || echo '\033[0m')
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
fi

OK_SYM="${GREEN}${BOLD} ✔ ${NC}"
WARN_SYM="${YELLOW}${BOLD} ⚠️ ${NC}"
FAIL_SYM="${RED}${BOLD} ✘ ${NC}"
INFO_SYM="${CYAN}${BOLD} ℹ️ ${NC}"

# --- 2. HELPER FUNCTIONS ---

# Function to safely curl and return only the HTTP status code
safe_curl_status() {
  # -k: Insecure, accepts self-signed certs (needed for local HTTPS/Traefik)
  # -s: Silent
  # -o /dev/null: Discard body
  # -w "%{http_code}": Write only the status code
  # --max-time 4: Timeout quickly
  curl -sk -o /dev/null -w "%{http_code}" --max-time 4 "$1" 2>/dev/null || echo "000"
}

# Function to pretty print status symbol based on HTTP code
pretty_status() {
  local code="$1"
  if [[ "$code" =~ ^2[0-9]{2}$ ]]; then
    printf "%b" "${OK_SYM}" # 2xx Success
  elif [[ "$code" =~ ^3[0-9]{2}$ ]]; then
    printf "%b" "${WARN_SYM}" # 3xx Redirection (OK, but noted)
  elif [[ "$code" == "000" ]]; then
    printf "%b" "${FAIL_SYM}" # Curl failed/Timeout
  else
    printf "%b" "${FAIL_SYM}" # Other errors (4xx, 5xx)
  fi
}

# Simple spinner fallback for refresh delay
simple_spinner() {
  local delay=0.15
  local chars="/-\|"
  local title="${1:-Refreshing...}"

  printf "${CYAN}%s${NC} " "$title"
  # Loop for 2 seconds
  for i in $(seq 1 14); do
    tput cub 1 # Cursor back 1
    printf "%s" "${chars:i%${#chars}:1}"
    sleep "$delay"
  done
  tput cub 1
  printf " "
}

# --- 3. CONFIGURATION & CLI FLAGS ---

REFRESH_INTERVAL=${REFRESH_INTERVAL:-2} # Default refresh interval (seconds)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-color) NO_COLOR=true; unset RED GREEN YELLOW BLUE CYAN BOLD NC; shift ;;
    -r|--refresh) REFRESH_INTERVAL="$2"; shift 2 ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--no-color] [-r|--refresh <seconds>]
  --no-color   Disable ANSI colors.
  -r, --refresh N  Refresh interval seconds (default ${REFRESH_INTERVAL}).
EOF
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

# Load .env variables (if present)
if [[ -f .env ]]; then
  # SC1090 is ignored as we expect .env file to be safe
  # shellcheck disable=SC1090
  set -a; source .env; set +a || true
fi

# --- SERVICES MAP (Define your service URLs) ---
declare -A SERVICES=(
  [Helix_API]="http://localhost:8000/health"
  [Keycloak]="https://keycloak.helix.local/realms/master"
  [Traefik_Dashboard]="https://traefik.helix.local/dashboard/"
  [MinIO_API]="http://127.0.0.1:9001/minio/health/live"
  [RabbitMQ_UI]="http://127.0.0.1:15672/api/aliveness-test/%2f" # Aliveness test URL
  [Vault]="https://vault.helix.local/v1/sys/health"
  [Grafana]="https://grafana.helix.local/api/health"
  [Prometheus]="http://127.0.0.1:9090/-/ready"
  [Ollama]="http://127.0.0.1:11434/api/tags" # Checks for model availability
  [Qdrant]="http://127.0.0.1:6333/readyz"
)

# --- 4. RENDER FUNCTIONS ---

# Header renderer
render_header() {
  local sha build_time host dockerv total_containers total_networks
  sha=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
  build_time=$(date '+%Y-%m-%d %H:%M:%S')
  host=$(hostname)
  dockerv=$(docker -v 2>/dev/null | cut -d',' -f1 || echo "Docker")
  # Use docker ps -a to count stopped containers too
  total_containers=$(docker ps -a -q | wc -l) 
  total_networks=$(docker network ls | wc -l)

  printf "${BOLD}${BLUE}"
  printf "╔════════════════════════════════════════════════════════════════════════╗\n"
  printf "║  🔐 HX DASHBOARD  •  %s  •  refresh %ss  •  host: %s\n" "${HX_PROJECT_APP_VERSION:-v24.0.4}" "${REFRESH_INTERVAL}" "${host}"
  printf "╚════════════════════════════════════════════════════════════════════════╝${NC}\n"
  printf "  ${INFO_SYM} System Info: %s | Git: %s | Containers: %s (Total) | Networks: %s\n\n" \
    "${dockerv}" "$sha" "$total_containers" "$total_networks"
}

# Single render cycle
render_cycle() {
  tput cup 0 0 || true # Move cursor to top left
  clear -x || true # Clear screen non-destructively

  render_header

  # --- SERVICE STATUS ---
  printf "%s\n" "${BLUE}${BOLD}--- 🌐 SERVICE HEALTH CHECK ---${NC}"
  for name in "${!SERVICES[@]}"; do
    url="${SERVICES[$name]}"
    code=$(safe_curl_status "$url")
    status_symbol=$(pretty_status "$code")
    
    # Print one-line status: SYMBOL name -> URL (code)
    printf "  %-3s %-20s → %s %s(%s)%s\n" "$status_symbol" "$name" "$url" "${BOLD}" "$code" "${NC}"
  done

  # --- DOCKER CONTAINERS STATUS ---
  echo
  printf "%s\n" "${BLUE}${BOLD}--- 🐳 DOCKER CONTAINER STATUS (Top 20) ---${NC}"
  # Print top 20 containers (running/healthy only)
  docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}" | sed -n '1,20p' | while IFS='|' read -r nm st img; do
    if [[ "$st" == *"(healthy)"* ]]; then
      status_symbol="${OK_SYM}"
    elif [[ "$st" == *"Up"* ]]; then
      status_symbol="${INFO_SYM}"
    elif [[ "$st" == *"Restarting"* ]]; then
      status_symbol="${WARN_SYM}"
    else
      status_symbol="${FAIL_SYM}"
    fi
    # Print one-line status: SYMBOL name -> Status (Image)
    printf "  %-3s %-20s → %s %s(%s)%s\n" "$status_symbol" "$nm" "$st" "${CYAN}" "$img" "${NC}"
  done

  # --- SYSTEM METRICS (for host) ---
  echo
  printf "%s\n" "${BLUE}${BOLD}--- 🌡️  SYSTEM METRICS ---${NC}"
  # Check if top/free/uptime are available before running
  if command -v top &>/dev/null && command -v free &>/dev/null && command -v uptime &>/dev/null; then
    CPU=$(top -bn1 | awk '/Cpu\(s\)/ {printf "%.0f%%", $2 + $4}')
    MEM=$(free -h | awk '/Mem:/ {print $3 "/" $2}')
    UP=$(uptime -p | sed 's/up //')
    printf "  🧠 CPU: %s | 💾 RAM: %s | ⏱️ Uptime: %s\n" "${CPU}" "${MEM}" "${UP}"
  else
    printf "  %s Basic system tools (top, free, uptime) not available.${NC}\n" "${WARN_SYM}"
  fi
  
  # --- LINKS FOOTER ---
  echo
  printf "%s\n" "${BLUE}------------------------------------------------------------${NC}"
  printf "  ${BOLD} LINKS:${NC} 📊 Grafana: https://grafana.helix.local | 🧠 Ollama: http://localhost:11434\n"
  printf "%s\n\n" "${BLUE}------------------------------------------------------------${NC}"
}

# --- 5. MAIN LOOP ---
# TUI safety / cleanup - reset cursor and terminal state on exit
trap 'tput cnorm 2>/dev/null || true; stty sane 2>/dev/null || true; clear 2>/dev/null || true' EXIT

# Hide cursor
tput civis 2>/dev/null || true

# Main loop
while true; do
  render_cycle
  
  # Use simple spinner for non-blocking refresh pause
  printf "\n"
  simple_spinner "📺 Refreshing in ${REFRESH_INTERVAL}s"
  sleep "$REFRESH_INTERVAL"
done