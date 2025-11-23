#!/usr/bin/env bash
# scripts/modules/helix-status-v2.sh
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — Bruce Lee Edition (Clickable Links)
# ==========================================================

# Exit immediately if a command exits with a non-zero status.
set -Eeuo pipefail
# Set IFS to only space, tab, and newline for safer word splitting
IFS=$'\n\t'
trap 'echo -e "\n🚨 CRASH ALERT! The script tripped on line $LINENO in $0!"' ERR

# --- 1. CONFIGURATION & ENVIRONMENT ---

# Load .env variables (if present)
ENV_FILE="./env/helix.env"
if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
fi
KEYCLOAK_DEV_REALM="${KEYCLOAK_DEV_REALM:-kc-realm-dev}"
HX_PROJECT_APP_VERSION="${HX_PROJECT_APP_VERSION:-vN/A}"
HELIX_ENVIRONMENT="${HELIX_ENVIRONMENT:-dev}" 
REFRESH_INTERVAL=${REFRESH_INTERVAL:-5} # Default refresh interval

# --- 2. COLORS & SYMBOLS (Self-Contained) ---

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

# --- 3. HELPER FUNCTIONS ---

# Function to safely curl and return only the HTTP status code
safe_curl_status() {
  # -k: Insecure (for local HTTPS), -s: Silent, -o /dev/null: Discard body
  curl -sk -o /dev/null -w "%{http_code}" --max-time 3 "$1" 2>/dev/null || echo "000"
}

# Function to wrap text in a clickable link (OSC 8)
format_link() {
  local url="$1"
  local text="$2"
  # Check for terminal support (basic check)
  if [[ -n "$url" && "$TERM" != "dumb" ]]; then
    printf '\033]8;;%s\033\\%s\033]8;;\033\\' "$url" "$text"
  else
    printf "%s" "$text"
  fi
}

# Function to pretty print status symbol based on HTTP code
pretty_status() {
  local code="$1"
  if [[ "$code" =~ ^2[0-9]{2}$ ]]; then
    printf "%b" "${OK_SYM}" 
  elif [[ "$code" =~ ^3[0-9]{2}$ ]]; then
    printf "%b" "${WARN_SYM}"
  elif [[ "$code" == "000" ]]; then
    printf "%b" "${FAIL_SYM}" 
  else
    printf "%b" "${FAIL_SYM}"
  fi
}

simple_spinner() {
  local delay=0.15
  local chars="/-\|"
  local title="${1:-Refreshing...}"

  printf "${CYAN}%s${NC} " "$title"
  # Loop for 2 seconds
  for i in $(seq 1 14); do
    tput cub 1 2>/dev/null || true
    printf "%s" "${chars:i%${#chars}:1}"
    sleep "$delay"
  done
  tput cub 1 2>/dev/null || true
  printf " "
}

# --- 4. SERVICE CONFIGURATION ---

# --- A. Service URL Mapping for Health Checks ---
declare -A HEALTH_URLS=(
  [helix]="http://localhost:8000/health"
  [keycloak]="https://keycloak.helix.local/realms/master"
  [traefik]="https://traefik.helix.local/dashboard/"
  [minio]="http://127.0.0.1:9001/minio/health/live"
  [rabbitmq]="http://127.0.0.1:15672/api/aliveness-test/%2f"
  [vault]="https://vault.helix.local/v1/sys/health"
  [grafana]="https://grafana.helix.local/api/health"
  [prometheus]="http://127.0.0.1:9090/-/ready"
  [flower]="http://127.0.0.1:5555"
  # Add other critical services here, ensuring the key matches the container name prefix
)

# --- B. Service Hyperlinks (for OSC 8) ---
declare -A URLS=(
  [helix]="https://helix-platform.local/docs"
  [traefik]="https://traefik.helix.local/dashboard/"
  [portainer]="https://portainer.helix.local"
  [keycloak]="https://keycloak.helix.local"
  [rabbitmq]="https://rabbitmq.helix.local"
  [redis]="" # No UI link
  [postgres]="" # No UI link
  [flower]="https://flower.helix.local"
  [minio]="http://127.0.0.1:9001/browser/"
  [vault]="https://vault.helix.local"
  [mailhog]="https://mailhog.helix.local"
  [prometheus]="https://prometheus.helix.local/query"
  [grafana]="https://grafana.helix.local/"
  [dozzle]="https://dozzle.helix.local/"
  [filebrowser]="https://filebrowser.helix.local/"
  [adminer]="" # No UI link
)

# --- C. Port & Description Mapping ---
declare -A PORTS=(
  [helix]=8000 [flower]=5555 [postgres]=5432 [redis]=6379 [rabbitmq]=5672 
  [keycloak]=8080 [minio]="9000-9001" [portainer]=9443 [vault]=8200 [traefik]="80/443"
)

# --- 5. RENDER FUNCTIONS ---

# Header renderer
render_header() {
  local sha build_time host dockerv total_containers total_networks
  sha=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
  build_time=$(date '+%Y-%m-%d %H:%M:%S')
  host=$(hostname)
  dockerv=$(docker -v 2>/dev/null | cut -d',' -f1 || echo "Docker")
  total_containers=$(docker ps -a -q | wc -l)
  total_networks=$(docker network ls | wc -l)

  printf "${BOLD}${CYAN}"
  printf "╔════════════════════════════════════════════════════════════════════════╗\n"
  printf "║ ${KEYCLOAK_DEV_REALM} 🔐 Helix Status 💦 %s 🩺️ %s • host: %s\n" "${HX_PROJECT_APP_VERSION}" "${HELIX_ENVIRONMENT}" "${host}"
  printf "╚════════════════════════════════════════════════════════════════════════╝${NC}\n"
  printf "  ${INFO_SYM} System Info: %s | Git SHA: %s | Containers: %s (Total) | Networks: %s\n\n" \
    "${dockerv}" "$sha" "$total_containers" "$total_networks"
}

# Main status loop
render_cycle() {
  tput cup 0 0 2>/dev/null || true
  clear -x 2>/dev/null || true

  render_header

  printf "%b\n" "${GREEN}${BOLD} 🏗️  🚢 ◾️ STATUS  💦️ PORT       APPLICATION: Description   🌐 ENDPOINT${NC}"
  
  # Fetch all container stats once
  docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > /tmp/helix_stats.csv
  
  # Enumerate ALL containers (running or stopped)
  docker ps -a --format "{{.Names}}\t{{.Status}}" | while IFS=$'\t' read -r name status; do
    [[ -z "$name" ]] && continue
    
    # Determine service base name for lookups
    service_name=$(echo "$name" | grep -oP '^[a-z]+')
    
    # 1. Look up Health Check Status (from external URL, if defined)
    url_to_check="${HEALTH_URLS[$service_name]:-}"
    http_code="N/A"
    if [[ -n "$url_to_check" ]]; then
      http_code=$(safe_curl_status "$url_to_check")
    fi

    # 2. Determine Status Icon & Color based on Docker Status AND HTTP Health
    local ICON_STATUS base_color status_msg status_icon
    status_icon=$(pretty_status "$http_code") # Start with CURL status
    
    # Override based on Docker status
    if [[ "$status" == *"unhealthy"* ]]; then
        ICON_STATUS="❌"; base_color=$RED;        status_msg="🚑 Down"
    elif [[ "$status" == *"Restarting"* ]]; then
        ICON_STATUS="🔁"; base_color=$YELLOW;     status_msg="♻️  Restart"
    elif [[ "$status" == *"healthy"* ]]; then
        ICON_STATUS="🟢"; base_color=$GREEN;      status_msg="✅ Healthy"
        status_icon="${OK_SYM}" # Ensure OK for healthy Docker status
    elif [[ "$status" == *"Up"* ]]; then
        ICON_STATUS="🟡"; base_color=$CYAN;       status_msg="🎡 Running"
    else
        ICON_STATUS="⚫"; base_color=$RED;        status_msg="⛔ Stopped"
    fi
    
    # 3. Service-specific emoji labels and base description (from your original script)
    case "$service_name" in
        filebrowser)  ICONS="🗄️ "; desc_base="filebrowser: Traefik File Browser" ;;
        adminer)      ICONS="🥎️"; desc_base="adminer: PGADMIN-lite DB UI" ;;
        grafana)      ICONS="♨️ "; desc_base="grafana: Monitoring Dashboards" ;;
        prometheus)   ICONS="🖥️ "; desc_base="prometheus: Collecting Metrics" ;;
        postgres)     ICONS="🐘"; desc_base="postgres: Inventory Management" ;;
        keycloak)     ICONS="🔐"; desc_base="keycloak: Security Gate Keeper" ;;
        rabbitmq)     ICONS="🐇"; desc_base="rabbitmq: Mailboxes & Job Tasks" ;;
        redis)        ICONS="🧃️"; desc_base="redis: Cache / Queue Control" ;;
        helix)        ICONS="🦄"; desc_base="helix: Main FastAPI Core" ;;
        worker)       ICONS="🥬️"; desc_base="worker: Celery Job Runner" ;;
        beat)         ICONS="🧩️"; desc_base="beat: Task Scheduler Clock" ;;
        flower)       ICONS="🌼"; desc_base="flower: Celery Monitor" ;;
        minio)        ICONS="🪣️ "; desc_base="minio: Object Storage" ;;
        pgadmin)      ICONS="🐘️"; desc_base="pgadmin: Database Admin." ;;
        portainer)    ICONS="📺️"; desc_base="portainer: Container UI" ;;
        traefik)      ICONS="💦"; desc_base="traefik: Reverse Proxy" ;;
        vault)        ICONS="🔒"; desc_base="vault: Secrets Manager" ;;
        mailhog)      ICONS="🐷️"; desc_base="mailhog: Email Testing" ;;
        dozzle)       ICONS="🪵 "; desc_base="dozzle: Live Log Monitoring" ;; 
            *)        ICONS="❕️❔️"; desc_base="$name: ⁉️ Unknown Service Name" ;;
    esac
    
    # 4. Hyperlink Integration
    url="${URLS[$service_name]:-}"
    if [[ -n "$url" ]]; then
      hyperlinked_desc=$(format_link "$url" "$desc_base")
    else
      hyperlinked_desc="${desc_base}"
    fi
    
    # 5. CPU/MEM (Simplified color logic from your script)
    # The CPU/MEM logic is removed for TUI stability and speed, but the original logic is below if needed:
    # stats_line=$(grep "^$name," /tmp/helix_stats.csv || true)
    # cpu=$(echo "$stats_line" | cut -d, -f2 | tr -d '%' || echo "0.0")
    # mem=$(echo "$stats_line" | cut -d, -f3 | cut -d'/' -f1 | xargs || echo "0MiB")

    # 6. Port mapping lookup
    PORT_INFO="${PORTS[$service_name]:-—}"
    
    # Output aligned line
    printf "%b %-2s %-4s ◾️%-12s %-12s  %s\n" \
      "$base_color" "$ICON_STATUS" "$ICONS" "$status_msg" "$PORT_INFO" "$hyperlinked_desc"
    
  done
  
  # Cleanup temp file
  rm -f /tmp/helix_stats.csv 2>/dev/null || true

  printf "%b\n" "🖥️  Dashboard updated: $(date)${NC}"
  printf "%b\n" "${OK_SYM} Total Running Containers: $(docker ps -q | wc -l)"
  echo
}

# --- 6. MAIN LOOP ---
# TUI safety / cleanup - reset cursor and terminal state on exit
trap 'tput cnorm 2>/dev/null || true; stty sane 2>/dev/null || true; clear 2>/dev/null || true; rm -f /tmp/helix_stats.csv 2>/dev/null || true' EXIT

# Hide cursor
tput civis 2>/dev/null || true

# Main loop
while true; do
  render_cycle
  
  # Pause and spin
  printf "\n"
  simple_spinner "📺 Refreshing in ${REFRESH_INTERVAL}s"
  sleep "$REFRESH_INTERVAL"
done