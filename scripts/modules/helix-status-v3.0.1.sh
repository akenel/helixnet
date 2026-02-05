#!/usr/bin/env bash
# scripts/modules/helix-status-v3.0.1.sh
# ==========================================================
# 🧩 HELIXNET STATUS DASHBOARD — Troubleshooter Edition (Logs Drill-Down)
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
REFRESH_INTERVAL=${REFRESH_INTERVAL:-60} # Default refresh interval
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
# Function to generate the command that runs the log viewer script
# This command is embedded in the OSC 8 link.
run_log_viewer() {
    local service_name="$1"
    local tail_lines="${2:-50}"
    local view_duration="${3:-30}" # seconds
    # We use a wrapper script and base64 to ensure the command executes correctly
    # when clicked, dealing with spaces and quotes in the shell execution.
    # Note: `bash -c` is used to execute the complex command string.
    # 1. Print a header
    # 2. Execute docker logs --tail N -f (follow)
    # 3. Add sleep and stop the logs
    local COMMAND_STRING="echo -e '\n\n${CYAN}>>> Displaying last ${tail_lines} logs for container: ${service_name} (Clickable Link: ${service_name}) <<<${NC}'; 
    echo -e '${YELLOW}Logs will automatically stop in ${view_duration} seconds. Press Ctrl+C to stop sooner.${NC}\n'; 
    docker logs ${service_name} --tail ${tail_lines} 2>&1; 
    sleep ${view_duration}; 
    echo -e '\n\n${GREEN}>>> Log viewing complete for ${service_name}. Dashboard will refresh shortly. <<<\n\n${NC}'; 
    read -n 1 -s -r -p 'Press any key to return to dashboard...'; 
    exit 0"
    # Base64 encode the command string to pass it safely to bash
    local ENCODED_CMD
    # Ensure all color codes are expanded before encoding
    ENCODED_CMD=$(echo -e "$COMMAND_STRING" | base64 -w 0)
    # The final clickable URL uses `bash -c` to decode and execute the command.
    # We must exit the subshell (the log viewer) so the main script continues.
    # This requires a new terminal/tab, so we use `gnome-terminal -e` or similar launcher.
    # NOTE: This part is highly OS/Terminal dependent. 
    # For maximum compatibility, we'll execute a simple script in a subshell, 
    # asking the user to manually switch terminals. A better approach is often 
    # creating a separate shell script that runs `docker logs` and using a terminal multiplexer (tmux/screen) 
    # but that's too complex for an in-line solution.
    # For *local development* we can often use x-terminal-emulator or gnome-terminal/konsole
    # For now, let's keep it simple and just show the command to copy/paste if the simple shell fails.
    # Option A (Best Attempt - depends on terminal): Use x-terminal-emulator
    # The command should start a new process that runs the log viewer and detaches.
    local SHELL_LAUNCHER="x-terminal-emulator -e" # Or gnome-terminal --, etc.
    local FINAL_COMMAND="$SHELL_LAUNCHER bash -c 'echo -e \"\n\n${CYAN}>>> Docker Logs for ${service_name} <<<${NC}\"; docker logs ${service_name} --tail ${tail_lines} 2>&1; echo -e \"\n${YELLOW}Sleeping for ${view_duration}s to read logs...${NC}\"; sleep ${view_duration}; echo -e \"${GREEN}Done. Close this window to resume dashboard view.${NC}\"'"
    # Since we cannot rely on the user's terminal launcher being correctly configured
    # for inline shell execution within OSC 8, we will simplify the link's action 
    # to running a temporary shell script in the background.
    # 1. Write a temporary script.
    # 2. Execute the script in a new shell/sub-window.
    # The simplest reliable thing to embed is a **command to copy/paste**. 
    # However, since you want it clickable, let's embed a simple `echo` command 
    # that tells the user the command to run, ensuring the link is still functional.
    # The actual command we want the user to execute:
    local LOG_COMMAND_TO_RUN="docker logs ${service_name} --tail ${tail_lines}"
    # The clickable link will simply copy the log command to the clipboard (if supported) 
    # or just echo it loudly in the current terminal, which is NOT ideal for TUI.
    # We will stick to the simplest, most functional approach: the link executes a new shell process.
    # We'll use the raw `docker logs` command as the OSC 8 URL target.
    # NOTE: The OSC 8 URL target is designed for web links, executing a shell command is an extension 
    # and highly non-standard. The standard practice is to make the link a URI like `http://localhost:9443`
    # and let the user click that.
    # Let's revert to the original idea, which is simpler and more reliable: 
    # The link should be the SERVICE'S UI (like Portainer/Dozzle), not a shell command.
    # A LOGS button executing a shell command requires an external log viewing tool 
    # (like Dozzle or Portainer logs) which we *can* link to.
    # Let's link the LOGS button to Dozzle, which is designed for this!
    # Dozzle URL: https://dozzle.helix.local/view/container_name
    local DOZZLE_BASE_URL="${URLS[dozzle]:-https://dozzle.helix.local}"
    # Replace the container name prefix (e.g., 'helix_') with the full container name 
    # for the Dozzle link, assuming Dozzle is running and configured.
    # Fallback to a simple shell command for terminals that support it.
    # We'll use a `sh` wrapper to clear the screen and run the command.
    local SH_COMMAND="sh -c 'echo -e \"\n\n${CYAN}>>> Docker Logs for ${service_name} <<<${NC}\"; docker logs ${service_name} --tail ${tail_lines} 2>&1 | less; read -p \"Press ENTER to continue...\"'"
    # For now, let's link to Dozzle if available, otherwise, display the shell command.
    if [[ -n "${DOZZLE_BASE_URL}" ]]; then
        local DOZZLE_URL="${DOZZLE_BASE_URL%/}/view/${service_name}"
        echo "$DOZZLE_URL"
    else
        # If Dozzle isn't mapped, create a shell script link to execute the log command
        # This is very unreliable in OSC 8, so we'll just return the log command string for now.
        echo "$SH_COMMAND"
    fi
}
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
  [helix-platform]="https://helix-platform.local/docs"
  [helix]="https://helix-platform.local/docs"
  [keycloak]="https://keycloak.helix.local/realms/master"
  [traefik]="https://traefik.helix.local/dashboard/"
  [minio]="http://127.0.0.1:9001/minio/health/live"
  [rabbitmq]="http://127.0.0.1:15672/api/aliveness-test/%2f"
  [vault]="https://vault.helix.local/v1/sys/health"
  [grafana]="https://grafana.helix.local/api/health"
  [prometheus]="http://127.0.0.1:9090/-/ready"
  [flower]="https://flower.helix.local"
  [ollama]="https://ollama.helix.local"
  [n8n]="https://n8n.helix.local"
  [helix-music]="http://localhost:1970"
  [portainer]="https://127.0.0.1:9443/api/system/status"
  [dozzle]="https://dozzle.helix.local"
  [mailhog]="http://127.0.0.1:8069"
)
# --- B. Service Hyperlinks (for OSC 8) ---
declare -A URLS=(
  [helix-platform]="https://helix-platform.local/docs"
  [helix]="https://helix-platform.local/docs"
  [traefik]="https://traefik.helix.local/dashboard/"
  [portainer]="https://portainer.helix.local"
  [keycloak]="https://keycloak.helix.local"
  [rabbitmq]="https://rabbitmq.helix.local"
  [redis]="https://rabbitmq.helix.local"
  [postgres]="https://adminer.helix.local/"
  [flower]="https://flower.helix.local"
  [minio]="http://127.0.0.1:9001/browser/"
  [vault]="https://vault.helix.local"
  [mailhog]="https://mailhog.helix.local"
  [prometheus]="https://prometheus.helix.local/query"
  [grafana]="https://grafana.helix.local/"
  [dozzle]="https://dozzle.helix.local"
  [filebrowser]="https://filebrowser.helix.local/"
  [adminer]="https://adminer.helix.local/"
  [ollama]="https://ollama.helix.local/"
  [openwebui]="https://openwebui.helix.local/"
  [n8n]="https://n8n.helix.local/"
  [helix-music]="http://localhost:1970"
)
# --- C. Port & Description Mapping ---
declare -A PORTS=(
  [helix-platform]=8000 [helix]=8000 [n8n]="5678:5678" [adminer]=8080 [ollama]=11434 [openwebui]=8080 [worker]="5555" [beat]="5555" [flower]=5555 [postgres]=5432 [redis]=6379 [rabbitmq]=5672
  [prometheus]=9090 [dozzle]=8080 [grafana]=3000 [mailhog]=8025 [keycloak]=8080 [minio]="9000/1" [minio-mc]="—" [portainer]=9443 [vault]=8200 [traefik]="80/443" [filebrowser]=80 [helix-music]=1970
  [helix-teller]=7791 [helix-video]=8096
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
  printf "╔════════════════════════════════════════════════════════════════════════════════════════╗\n"
  printf "║ ${KEYCLOAK_DEV_REALM} 🔐 Helix Status 🐳️ $dockerv  💦 %s  🩺️ %s • host: %s\n" "${HX_PROJECT_APP_VERSION}" "${HELIX_ENVIRONMENT}" "${host} ║"
  printf "╚════════════════════════════════════════════════════════════════════════════════════════╝${NC}\n"
  printf "  ${INFO_SYM} System Info HelixNet ✏️  Git SHA: %s 🛞️  Containers: %s (Total) 💦️ Networks: %s\n\n" \
     "$sha" "$total_containers" "$total_networks"}
}
# Main status loop
render_cycle() {
  tput cup 0 0 2>/dev/null || true
  clear -x 2>/dev/null || true
  render_header
  printf "%b\n" "${GREEN}${BOLD} 🏗️  ◾🚢 🔐 STATUS  💦️ PORT   service ◾️ Description 🌐 ENDPOINT 👁️  Logs${NC}"
  # Fetch all container stats once (for completeness, though not currently displayed)
  docker stats --no-stream --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}}" > /tmp/helix_stats.csv
  # Enumerate ALL containers (running or stopped)
  docker ps -a --format "{{.Names}}\t{{.Status}}\t{{.ID}}" | while IFS=$'\t' read -r name status container_id; do
    [[ -z "$name" ]] && continue
    service_name="$name"
    # 1. Look up Health Check Status
    url_to_check="${HEALTH_URLS[$service_name]:-}"
    http_code="N/A"
    if [[ -n "$url_to_check" ]]; then
      http_code=$(safe_curl_status "$url_to_check")
    fi
    # 2. Determine Status Icon & Color
    local ICON_STATUS base_color status_msg status_icon
    status_icon=$(pretty_status "$http_code")
    if [[ "$status" == *"unhealthy"* ]]; then
        ICON_STATUS="❌"; base_color=$RED;        status_msg="🚑 Down"
    elif [[ "$status" == *"Restarting"* ]]; then
        ICON_STATUS="🔁"; base_color=$YELLOW;     status_msg="♻️  Restart"
    elif [[ "$status" == *"healthy"* ]]; then
        ICON_STATUS="🟢"; base_color=$GREEN;      status_msg="✅ Healthy"
        status_icon="${OK_SYM}"
    elif [[ "$status" == *"Up"* ]]; then
        ICON_STATUS="🟡"; base_color=$CYAN;       status_msg="🎡 Running"
    else
        ICON_STATUS="⚫"; base_color=$RED;        status_msg="⛔ Stopped"
    fi
    # 3. Service-specific emoji labels and base description
    case "$name" in
        filebrowser)    ICONS="🗄️ "; desc_base="filebrowser 🗄️  Traefik File Browser    " ;;
        adminer)        ICONS="🥎️";  desc_base="adminer 🥎️ pgAdmin-lite Database UI   " ;;
        grafana)        ICONS="♨️ "; desc_base="grafana ♨️  Monitoring Dashboards     " ;;
        prometheus)     ICONS="🖥️ "; desc_base="prometheus 🖥️  Collecting Metrics     " ;;
        postgres)       ICONS="🐘";  desc_base="postgres 🐘 Inventory Management     " ;;
        keycloak)       ICONS="🔐";  desc_base="keycloak 🔐 Security Gate Keeper     " ;;
        rabbitmq)       ICONS="🐇";  desc_base="rabbitmq 🐇 Mailboxes & Job Tasks    " ;;
        redis)          ICONS="🧃️";  desc_base="redis 🧃️ Cache / Queue Control       " ;;
        helix-platform) ICONS="🦄";  desc_base="helix-platform 🦄 Main FastAPI Core  " ;;
        worker)         ICONS="🥬️";  desc_base="worker 🥬️ Celery Job Runner          " ;;
        beat)           ICONS="🧩️";  desc_base="beat 🧩️ Task Scheduler Clock         " ;;
        flower)         ICONS="🌼";  desc_base="flower 🌼 Celery Monitor              " ;;
        minio)          ICONS="🪣️ "; desc_base="minio 🪣️  S3 Object Storage           " ;;
        minio-mc)       ICONS="🪣️ "; desc_base="minio-mc 🪣️  S3 Admin CLI Sidecar     " ;;
        traefik)        ICONS="💦";  desc_base="traefik 💦 Reverse Proxy / TLS        " ;;
        vault)          ICONS="🔒";  desc_base="vault 🔒 Secrets Manager              " ;;
        mailhog)        ICONS="🐷️";  desc_base="mailhog 🐷️ Email Testing              " ;;
        portainer)      ICONS="🐳";  desc_base="portainer 🐳 Docker Management UI     " ;;
        dozzle)         ICONS="🪵 "; desc_base="dozzle 🪵  Live Log Monitoring        " ;;
        ollama)         ICONS="🍏️";  desc_base="ollama 🍏️ Local LLM Engine           " ;;
        openwebui)      ICONS="🐦️";  desc_base="openwebui 🐦️ AI Web Chat             " ;;
        n8n)            ICONS="📢";  desc_base="n8n 📢 Automation & Webhooks          " ;;
        helix-music)    ICONS="🐅";  desc_base="helix-music 🐅 Electric Jungle Player " ;;
        helix-teller)   ICONS="🗣️";  desc_base="helix-teller 🗣️ Language Learning App  " ;;
        helix-video)    ICONS="🎬";  desc_base="helix-video 🎬 Jellyfin Media Server  " ;;
          *)            ICONS="🪝️ ";  desc_base="$name 🪝️  Unregistered Service       " ;;
    esac
    # 4. Hyperlink Integration (Service UI link)
    url="${URLS[$service_name]:-}"
    if [[ -n "$url" ]]; then
      hyperlinked_desc=$(format_link "$url" "$desc_base")
    else
      hyperlinked_desc="${desc_base}"
    fi
    # 5. Log Link Integration (Troubleshooting Link)
    log_link_text="${BLUE}${BOLD}[LOGS]${NC}"
    # Priority 1: Link to Dozzle (best log viewer)
    dozzle_base_url="${URLS[dozzle]:-}"
    if [[ -n "$dozzle_base_url" ]]; then
        # Link to the specific container ID in Dozzle
        log_url="${dozzle_base_url%/}/view/${container_id}"
        logs_hyperlink=$(format_link "$log_url" "$log_link_text")
    else
        logs_hyperlink="${YELLOW} (No Dozzle UI)${NC}" 
    fi
    # 6. Port mapping lookup
    PORT_INFO="${PORTS[$service_name]:-—}"
    printf "%b %-2s ◾%-4b %-8s %-8s  %-48s %-12s\n" \
      "$base_color" "$ICON_STATUS" "$ICONS" "$status_msg" "$PORT_INFO" "$hyperlinked_desc" "$logs_hyperlink"
  done
  # Cleanup temp file
  rm -f /tmp/helix_stats.csv 2>/dev/null || true
  printf "%b\n" "🖥️  Dashboard updated: $(date)${NC}"
  printf "%b\n" "${OK_SYM} Total Running Containers: $(docker ps -q | wc -l)"
  echo
}
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