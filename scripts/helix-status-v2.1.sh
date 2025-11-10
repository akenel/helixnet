#!/usr/bin/env bash
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — Sherlock Forge Edition
# ==========================================================
set -Eeuo pipefail
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in $0!"' ERR

# --- Colors ---
RED='\e[31m'; GREEN='\e[32m'; YELLOW='\e[33m'; CYAN='\e[36m'; BOLD='\e[1m'; NC='\e[0m'

# --- OSC 8 Clickable Link Formatter ---
format_link() {
  local text="$1"; local url="$2"
  [[ -n "$url" ]] && printf "\e]8;;%s\e\\%s\e]8;;\e\\" "$url" "$text" || printf "%s" "$text"
}

# --- URLs ---
declare -A URLS=(
  [helix]="https://helix.local/docs"
  [traefik]="https://traefik.helix.local/dashboard/"
  [portainer]="https://portainer.helix.local"
  [keycloak]="https://keycloak.helix.local"
  [rabbitmq]="https://rabbitmq.helix.local"
  [redis]="https://redis.helix.local"
  [flower]="https://flower.helix.local"
  [minio]="http://127.0.0.1:9001/browser/"
  [vault]="https://vault.helix.local"
  [mailhog]="https://mailhog.helix.local"
  [prometheus]="https://prometheus.helix.local/query"
  [grafana]="https://grafana.helix.local/"
)

# --- Ports ---
declare -A PORTS=(
  [helix]=8000 [flower]=5555 [postgres]=5432 [redis]=6379 [rabbitmq]=5672 [mailhog]=8025
  [keycloak]=8080 [minio]="9000-9001" [portainer]=9443 [prometheus]=9090 [grafana]=3000
  [vault]=8200 [traefik]="80/443"
)

# --- Header ---
printf "\n${CYAN}${BOLD}🧩 Helixnet Shipyard Container 'DEV' Port ${GREEN}🏗️  ◾ 🚢 ◾ 💦${NC}\n"
printf "${GREEN}${BOLD} ⏲️  ◾ $(date)        on ◾ $(hostname)${NC}\n\n"
printf "${CYAN}🧱 Build: $(date '+%Y-%m-%d %H:%M') | Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'local')${NC}\n\n"
printf "${BOLD}${CYAN} 🏗️  🚢 ◾🩺 Status 💦 Port   🧮 CPU  🧠 Mem   Container: Application ◾ 🧩 Endpoint${NC}\n\n"

# --- Grab stats once ---
docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > /tmp/helix_stats.csv

# --- Categorization labels ---
printf "${YELLOW}${BOLD}🏗️  CORE APPLICATION LAYER${NC}\n"

core_services=(helix worker beat flower keycloak)
infra_services=(postgres redis traefik vault filebrowser grafana portainer minio rabbitmq mailhog prometheus)

# --- Function to render a service line ---
render_service() {
  local name="$1"
  [[ -z "$name" ]] && return

  service_name=$(echo "$name" | grep -oP '^[a-z]+')
  stats_line=$(grep "^$name," /tmp/helix_stats.csv || true)
  cpu=$(echo "$stats_line" | cut -d, -f2 | tr -d '%' || echo "0.0")
  mem=$(echo "$stats_line" | cut -d, -f3 | cut -d'/' -f1 | xargs || echo "0MiB")

  # Choose color by CPU %
  cpu_num=${cpu%.*}
  if (( cpu_num > 70 )); then cpu_color=$RED
  elif (( cpu_num > 20 )); then cpu_color=$YELLOW
  else cpu_color=$GREEN; fi
  CPU_STR="${cpu_color}${cpu}%${NC}"

  # Memory color tone (rough estimate)
  [[ "$mem" == *GiB* ]] && mem_color=$RED || mem_color=$GREEN
  MEM_STR="${mem_color}${mem}${NC}"

  # Get Docker status
  status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "none")

  case "$status" in
    healthy) ICON_STATUS="🟢"; status_msg="✅ Healthy"; base_color=$GREEN ;;
    unhealthy) ICON_STATUS="❌"; status_msg="🚑 Down"; base_color=$RED ;;
    starting) ICON_STATUS="🟡"; status_msg="♻️ Restarting"; base_color=$YELLOW ;;
    *) ICON_STATUS="⚫"; status_msg="⛔ Stopped"; base_color=$RED ;;
  esac

  case "$service_name" in
    filebrowser) ICONS="🗄️ "; desc="filebrowser: Traefik File Browser" ;;
    adminer) ICONS="🥎 "; desc="adminer: PGADMIN-lite DB UI" ;;
    grafana) ICONS="♨️ "; desc="grafana: Monitoring Dashboards" ;;
    prometheus) ICONS="🖥️ "; desc="prometheus: Collecting Metrics" ;;
    postgres) ICONS="🐘 "; desc="postgres: Inventory Management" ;;
    keycloak) ICONS="🔐 "; desc="keycloak: Security Gate Keeper" ;;
    rabbitmq) ICONS="🐇 "; desc="rabbitmq: Mailboxes & Jobs" ;;
    redis) ICONS="🧃 "; desc="redis: Cache / Queue Control" ;;
    helix) ICONS="🦄 "; desc="helix: Main FastAPI Core" ;;
    worker) ICONS="🥬 "; desc="worker: Celery Job Runner" ;;
    beat) ICONS="🧩 "; desc="beat: Task Scheduler Clock" ;;
    flower) ICONS="🌼 "; desc="flower: Celery Monitor" ;;
    minio) ICONS="📦 "; desc="minio: Object Storage" ;;
    portainer) ICONS="📺 "; desc="portainer: Container UI" ;;
    traefik) ICONS="💦 "; desc="traefik: Reverse Proxy" ;;
    vault) ICONS="🔒 "; desc="vault: Secrets Manager" ;;
    mailhog) ICONS="🐷 "; desc="mailhog: Mail Tester" ;;
    *) ICONS="❓ "; desc="$name: Unknown" ;;
  esac

  url="${URLS[$service_name]:-}"
  [[ -n "$url" ]] && endpoint="→ $(format_link "${CYAN}${url}${NC}" "$url")" || endpoint=""

  PORT_INFO="${PORTS[$service_name]:-—}"

  printf "${base_color}%s %-3s %-10s %-8s %-8s %-35s %b${NC}\n" \
    "$ICON_STATUS" "$ICONS" "$status_msg" "$PORT_INFO" "$CPU_STR" "$desc" "$endpoint"
}

# --- Render core layer ---
for s in "${core_services[@]}"; do
  c=$(docker ps --format '{{.Names}}' | grep -E "^$s" || true)
  [[ -n "$c" ]] && render_service "$c"
done

printf "\n${YELLOW}${BOLD}🧩  INFRASTRUCTURE & MONITORING${NC}\n"
for s in "${infra_services[@]}"; do
  c=$(docker ps --format '{{.Names}}' | grep -E "^$s" || true)
  [[ -n "$c" ]] && render_service "$c"
done

# --- Summary footer ---
printf "\n${CYAN}--------------------------------------------------------------------------------------${NC}\n"
printf "🖥️  Dashboard updated: %s\n" "$(date)"
printf "✅ Total containers: %s (includes Restarting and Healthy ones)\n" "$(docker ps -q | wc -l)"
printf "🟢 = Healthy  |  ❌ = Down  |  🟡 = Restarting  |  ⚫ = Stopped\n"
echo ""
