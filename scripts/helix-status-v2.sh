#!/usr/bin/env bash
# scripts/helix-status.sh
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — Sherlock Edition (Hyperlinked)
# ==========================================================
set -Eeuo pipefail
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR

# --- Colors & Emojis ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# --- Link Escape Sequence (OSC 8) ---
# Format: \033]8;;URL\033\\TEXT\033]8;;\033\\
# This function wraps text in a clickable link if the terminal supports OSC 8
format_link() {
  local url="$1"
  local text="$2"
  if [[ -n "$url" ]]; then
    printf "%s" "$url" "$text"
  else
    printf "%s" "$text"
  fi
}

# --- Service URL Mapping (The links you wanted to embed) ---
declare -A URLS=(
  [helix]=" 🦄 https://helix.local/docs"
  [traefik]=" 💦 https://traefik.helix.local/dashboard/"
  [portainer]=" 📺️ https://portainer.helix.local"
  [keycloak]=" 🔐 https://keycloak.helix.local"
  [rabbitmq]=" 🐇 https://rabbitmq.helix.local"
  [redis]=" 🧃️ https://redis.helix.local"
  [flower]=" 🌼 https://flower.helix.local"
  [minio]=" 📦 http://127.0.0.1:9001/browser/"
  [vault]=" 🔒 https://vault.helix.local"
  [mailhog]=" 🐷️ https://mailhog.helix.local"
  [prometheus]=" 🖥️  https://prometheus.helix.local/query"
  [grafana]=" ♨️  https://grafana.helix.local/"


  # Note: Worker and Beat typically have no external UI, so they are excluded.
)

printf "%b\n" "${CYAN}${BOLD}🧩 Helixnet Shipyard Container 'DEV' Port ${GREEN} 🏗️  ◾️ 🚢 ◾️ 💦${NC}"
printf "%b\n" "${GREEN}${BOLD} ⏲️  ◾️ $(date)        on ◾️ $(hostname)${NC}"

# Removing the verbose list of links here, keeping the output clean.
# printf "\n"
# printf "%b\n" "${CYAN}  🔍 Sorting by CPU (Top First)${NC}"
printf "%b\n" "${GREEN}${BOLD} 🏗️  🚢 ◾️🩺️ Status  💦️ Port       container: Application ◾️ 🧩 endpoint${NC}"

# --- Known Ports ---
declare -A PORTS=(
  [helix]=8000 [flower]=5555 [postgres]=5432 [redis]=6379 [rabbitmq]=5672 [mailhog]=8025 
  [keycloak]=8080 [minio]="9000-9001" [portainer]=9443 [prometheus]=9090 [grafana]=3000
  [vault]=8200 [traefik]="80/443"
)

# --- Get live stats ---
# Note: /tmp is generally safe for temporary files in Linux/macOS
docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > /tmp/helix_stats.csv

# --- Enumerate ALL containers ---
docker ps -a --format "{{.Names}}\t{{.Status}}" | while IFS=$'\t' read -r name status; do
  [[ -z "$name" ]] && continue

  # Determine service base name for lookups
  service_name=$(echo "$name" | grep -oP '^[a-z]+')

  # Extract CPU & Memory (fallback if missing)
  stats_line=$(grep "^$name," /tmp/helix_stats.csv || true)
  cpu=$(echo "$stats_line" | cut -d, -f2 | tr -d '%' || echo "0.0")
  mem=$(echo "$stats_line" | cut -d, -f3 | cut -d'/' -f1 | xargs || echo "0MiB")

  # Determine status icon & color
  if [[ "$status" == *"unhealthy"* ]]; then
      ICON_STATUS="❌"; base_color=$RED;        status_msg="🚑 Down  ◾️◾️"
  elif [[ "$status" == *"Restarting"* ]]; then
      ICON_STATUS="🔁"; base_color=$YELLOW;     status_msg="♻️  Restart 👀️"
  elif [[ "$status" == *"healthy"* ]]; then
      ICON_STATUS="🟢"; base_color=$GREEN;      status_msg="✅ Healthy ◾️"
  elif [[ "$status" == *"Up"* ]]; then
      ICON_STATUS="🟡"; base_color=$CYAN;       status_msg="🎡 Running ◾️"
  else
      ICON_STATUS="⚫"; base_color=$RED;        status_msg="⛔ Stopped 👀️"
  fi

  # Service-specific emoji labels and base description
  case "$service_name" in
    filebrowser)  ICONS="🗄️ "; desc_base="filebrowser: Traefik File Browser" ;;
    adminer)      ICONS="🥎️"; desc_base="adminer: PGADMIN-lite DB UI" ;;
    grafana)      ICONS="♨️ "; desc_base="grafana: Monitoring Dashboards" ;;
    prometheus)   ICONS="🖥️ "; desc_base="prometheus: Collecting Metrics" ;;
    postgres)     ICONS="🐘"; desc_base="postgres: Inventory Management" ;;
    keycloak)     ICONS="🔐"; desc_base="keycloak: Security Gate Keeper" ;;
    rabbitmq)     ICONS="🐇"; desc_base="rabbitmq: Mailboxes & Jobs" ;;
    redis)        ICONS="🧃️"; desc_base="redis: Cache / Queue Control" ;;
    helix)        ICONS="🦄"; desc_base="helix: Main FastAPI Core" ;;
    worker)       ICONS="🥬️"; desc_base="worker: Celery Job Runner" ;;
    beat)         ICONS="🧩️"; desc_base="beat: Task Scheduler Clock" ;;
    flower)       ICONS="🌼"; desc_base="flower: Celery Monitor" ;;
    minio)        ICONS="📦"; desc_base="minio: Object Storage" ;;
    pgadmin)      ICONS="🐘️"; desc_base="pgadmin: Database Admin." ;;
    portainer)    ICONS="📺️"; desc_base="portainer: Container UI" ;;
    traefik)      ICONS="💦"; desc_base="traefik: Reverse Proxy" ;;
    vault)        ICONS="🔒"; desc_base="vault: Secrets Manager" ;;
    mailhog)      ICONS="🐷️"; desc_base="mailhog: Secrets Manager" ;;

        *)            ICONS="❓"; desc_base="$name: Unknown" ;;
  esac

  # --- Hyperlink Integration ---
  url="${URLS[$service_name]:-}"
  # Check if a URL exists and create the hyperlinked description string
  if [[ -n "$url" ]]; then
    # Use the function to embed the OSC 8 link
    hyperlinked_desc=$(format_link   "$desc_base"  "$url")
  else
    hyperlinked_desc="  $desc_base"
  fi

  # CPU/MEM color intensity
  cpu_num=${cpu%.*}
  [[ -z "$cpu_num" ]] && cpu_num=0
  if (( cpu_num > 70 )); then cpu_color=$RED
  elif (( cpu_num > 20 )); then cpu_color=$YELLOW
  else cpu_color=$GREEN; fi
  CPU_STR="${cpu_color}${cpu}%${NC}"

  # Port mapping lookup
  PORT_INFO="${PORTS[$service_name]:-—}"

  # Output aligned line (using printf -v to capture the description width) 
  printf "%b %-2s %-4s ◾️%-16s %-9s  %-40s \n" \
      "$base_color" "$ICON_STATUS" "$ICONS" "$status_msg" "$PORT_INFO" "$hyperlinked_desc"

done

printf "\n%b%s\n" "${CYAN}" "-----------------------------------------------------------------------------------------------------"
printf "%b\n" "🖥️  Dashboard updated: $(date)"
printf "%b\n" "✅ Total containers: $(docker ps -q | wc -l)  (includes Restarting and Healthy ones)"
echo
