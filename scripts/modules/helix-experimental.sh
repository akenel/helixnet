#!/usr/bin/env bash
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — script (v3.1) Edition
# ==========================================================
# FIX: Refactored output loop to use multiple printf statements for stable column width
# despite embedded color codes and OSC8 hyperlinks.

set -euo pipefail

trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in $0!"' ERR

# --- Colors --- Set colors for output
CHECK="✔️"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
CYAN='\033[0;39m'
NC='\033[0m' # No Color
BOLD="\033[1m"; RESET="\033[0m"
OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; WARN="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
# ==========================================================
# 🖌️  Color / Emoji Control
# ==========================================================
NO_COLOR=false
for arg in "$@"; do
  case "$arg" in
    --no-color) NO_COLOR=true ;;
  esac
done

if $NO_COLOR; then
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; NC=''
  BOLD=''; RESET=''; OK='OK'; FAIL='FAIL'; SKIP='SKIP'; INFO='INFO'
else
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
  BLUE='\033[0;36m'; CYAN='\033[0;39m'; NC='\033[0m'
  BOLD='\033[1m'; RESET='\033[0m'
  OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"
  SKIP="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
fi

# --- OSC8 Hyperlink Function ---
format_link() {
  local text="$1"; local url="$2"
  [[ -n "$url" ]] && printf "\033]8;;%s\033\\%s\033]8;;\033\\" "$url" "$text" || printf "%s" "$text"
}
    echo "╔═════════════════════════════════════════════╗"
    echo "║ $KEYCLOAK_DEV_REALM 🔐 HelixNet  💦 v${HX_PROJECT_APP_VERSION} 🩺️ $HELIX_ENVIRONMENT ║"
    echo "╚════════> ./scripts/helix-status.sh <════════╝"

# --- URLs (Used for OSC8 Links) ---
declare -A URLS=(
  [helix]="https://helix-platform.local/docs"
  [mailhog]="http://mailhog.helix.local:8025"
  [traefik]="https://traefik.helix.local/dashboard/"
  [portainer]="https://portainer.helix.local"
  [keycloak]="https://keycloak.helix.local"
  [rabbitmq]="https://rabbitmq.helix.local"
  [redis]="https://redis.helix.local"
  [flower]="https://flower.helix.local"
  [minio]="http://127.0.0.1:9001/browser/"
  [vault]="https://vault.helix.local"
)

# --- Ports ---
declare -A PORTS=(
  [helix]=8000 [flower]=5555 [postgres]=5432 [redis]=6379 [rabbitmq]=5672
  [keycloak]=8080 [minio]="9000-9001" [portainer]=9443 [vault]=8200 [traefik]="80/443"
)

# --- Header ---
printf "%b\n" "${CYAN}${BOLD}🧩 Helixnet Shipyard Status — DEV 🏗️  🚢 💦${NC}"
printf "%b\n" "${GREEN}${BOLD}⏲️ $(date) on $(hostname)${NC}"

printf "\n%b\n" "${CYAN}${BOLD}🔍 Sorted by CPU Usage (Top First)${NC}"

# Define the format for the header and use it to print the labels
HEADER_FORMAT="%s %-15s %-15s %-10s %-7s %-7s %-10s %s\n"
printf "%b$HEADER_FORMAT" "$BOLD" "ICON/NAME" "STATUS" "PORT" "CPU" "MEM" "HEALTH" "DESCRIPTION" "$NC"
printf "%b\n" "${CYAN}------------------------------------------------------------------------------------------${NC}"

# --- 1. Capture docker stats and status ---
# Stats: Container,CPUPerc,MemUsage
docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > /tmp/helix_stats.csv

# Status: Names,Status
mapfile -t containers < <(docker ps -a --format "{{.Names}}\t{{.Status}}")

# --- 2. Build an array of "CPU|NAME|STATUS|MEM" triples ---
rows=()
for entry in "${containers[@]}"; do
  name=$(echo "$entry" | cut -f1)
  status_text=$(echo "$entry" | cut -f2)
  [[ -z "$name" ]] && continue

  stats_line=$(grep "^$name," /tmp/helix_stats.csv || true)
  cpu=$(echo "$stats_line" | cut -d, -f2 | tr -d '%')
  mem=$(echo "$stats_line" | cut -d, -f3)

  [[ -z "$cpu" ]] && cpu=0.0
  [[ -z "$mem" ]] && mem="0B"
  
  rows+=("${cpu}|${name}|${status_text}|${mem}")
done

# --- 3. Sort rows by numeric CPU descending ---
IFS=$'\n' sorted_rows=($(sort -t'|' -k1,1nr <<<"${rows[*]}"))
unset IFS

# --- 4. Now loop over sorted rows and print the final table ---
for row in "${sorted_rows[@]}"; do
  # Extract fields
  cpu=$(echo "$row" | cut -d'|' -f1)
  name=$(echo "$row" | cut -d'|' -f2)
  status_text=$(echo "$row" | cut -d'|' -f3)
  mem=$(echo "$row" | cut -d'|' -f4)

  # --- A. Health, Icon, Color ---
  if [[ "$status_text" == *"unhealthy"* ]]; then
      ICON="❌"; ROW_COLOR=$RED; HEALTH="Unhealthy"
  elif [[ "$status_text" == *"Restarting"* ]]; then
      ICON="🔁"; ROW_COLOR=$YELLOW; HEALTH="Restart"
  elif [[ "$status_text" == *"healthy"* ]]; then
      ICON="🟢"; ROW_COLOR=$GREEN; HEALTH="Healthy"
  elif [[ "$status_text" == *"Up"* ]]; then
      ICON="🟡"; ROW_COLOR=$CYAN; HEALTH="Running"
  else
      ICON="⚫"; ROW_COLOR=$RED; HEALTH="Stopped"
  fi

  # --- B. Emojis & Description ---
  case "$name" in
    postgres)  EMOJI="🐘"; DESC="PostgreSQL Database" ;;
    mailhog)   EMOJI="🐷️"; DESC="MailHog SMTP Server" ;;
    keycloak)  EMOJI="🔐"; DESC="Identity & Auth Server" ;;
    rabbitmq)  EMOJI="🐇"; DESC="Message Broker" ;;
    redis)     EMOJI="🧃"; DESC="Cache & Queue" ;;
    helix)     EMOJI="🦄"; DESC="FastAPI Core Service" ;;
    worker)    EMOJI="🥬"; DESC="Celery Job Worker" ;;
    beat)      EMOJI="🧩"; DESC="Celery Scheduler" ;;
    flower)    EMOJI="🌼"; DESC="Celery Monitor UI" ;;
    minio)     EMOJI="🪣️  "; DESC="Object Storage" ;;
    portainer) EMOJI="📺"; DESC="Container UI" ;;
    traefik)   EMOJI="💦"; DESC="Reverse Proxy" ;;
    vault)     EMOJI="🔒"; DESC="Secrets Manager" ;;
    *)         EMOJI="❓"; DESC="Unknown Service" ;;
  esac

  # --- C. Final Formatting ---
  # CPU coloring
  cpu_val=${cpu%.*}
  CP_COLOR=$GREEN
  if (( cpu_val > 70 )); then CP_COLOR=$RED
  elif (( cpu_val > 20 )); then CP_COLOR=$YELLOW; fi

  # Memory trimming (remove spaces and newlines)
  MEM_STR=$(echo "$mem" | sed 's/ //g' | tr -d '\n')
  
  # Port
  PORT_STR=${PORTS[$name]:-—}
  
  # Link (if exists)
  LINK="${URLS[$name]:-}"
  DESCRIPTION_OUTPUT=$(format_link "$DESC" "$LINK")

  # --- D. Output the single, well-formatted row (Multi-printf method) ---
  # Start the line with the row color
  printf "%b" "$ROW_COLOR" 
  
  # ICON/NAME
  printf "%-15s" "$EMOJI $name" 
  
  # STATUS
  printf "%-15s" "$status_text"
  
  # PORT
  printf "%-10s" "$PORT_STR"
  
  # CPU (Colored, padded, and reset before next column)
  printf "%b%-7s%b" "$CP_COLOR" "$cpu%" "$ROW_COLOR"
  
  # MEM
  printf "%-7s" "$MEM_STR"
  
  # HEALTH
  printf "%-10s" "$HEALTH"
  
  # DESCRIPTION (Contains the OSC8 link and implicitly ends the row)
  printf "%s\n" "$DESCRIPTION_OUTPUT"

  # Reset color just in case
  printf "%b" "$NC" 
done

printf "%b\n" "${CYAN}------------------------------------------------------------------------------------------${NC}"
printf "%b\n" "${BOLD}🖥️  Dashboard updated: $(date)  |  Total Containers: $(docker ps -q | wc -l)${NC}\n"
sleep 20