#!/usr/bin/env bash
# =============================================================
# 🧭 HelixNet Control Center - Interactive TUI (v4.2 SHERLOCK)
# =============================================================
# - Polished: networks -> volumes -> image -> menu
# - Gum-safe, Docker-safe, idempotent
# =============================================================
set -o errexit
set -o nounset
set -o pipefail
IFS=$'\n\t'
# -------------------------------------------------------------
# Terminal safety: Fixes "unbound variable" crash
# We use ${VAR:-} to safely check for unset variables
# -------------------------------------------------------------
# ===== Does Term support clickable links ======================
if [[ "${TERM_PROGRAM:-}" != "iTerm.app" && ! "${WT_SESSION:-}" ]]; then
    echo "⚠️  Terminal does not fully support clickable links — showing plain text mode."
fi
# === HEALTHCHECK_SUPPORTED (placeholder, assumes helper is sourced later) ==================
HEALTHCHECK_SUPPORTED=true 

# -------------------------------------------------------------
# CLI Flags
# -------------------------------------------------------------
DRY_RUN=false
ONLY_CORE=false
ONLY_MAIN=false
ONLY_LLM=false

for arg in "$@"; do
  
  if [[ "${1:-}" == "--help" ]]; then
        echo "
      Helix Control Center Flags
        --dry-run     Show docker commands without running them
        --only-core   Boot only: DB, Traefik, Keycloak, Redis, Postgres
        --only-main   Boot only: API stack (depends on core existing)
        --only-llm    Boot only: Ollama, OpenWebUI stack
      "
        exit 0
      fi
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --only-core) ONLY_CORE=true ;;
    --only-main) ONLY_MAIN=true ;;
    --only-llm) ONLY_LLM=true ;;
  esac
done
# -------------------------------------------------------------
# Resolve repo paths
# -------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="${ROOT_DIR}/scripts/tools"
MODULES_DIR="${ROOT_DIR}/scripts/modules"
SETUP_DIR="${MODULES_DIR}/setup"

# -------------------------------------------------------------
# Load helpers if available (non-fatal)
# -------------------------------------------------------------
[[ -f "${TOOLS_DIR}/helix-utils.sh" ]] && source "${TOOLS_DIR}/helix-utils.sh" || true
[[ -f "${TOOLS_DIR}/helix-common.sh" ]] && source "${TOOLS_DIR}/helix-common.sh" || true
[[ -f "${TOOLS_DIR}/sys-checks.sh" ]] && source "${TOOLS_DIR}/sys-checks.sh" || true
[[ -f "${SETUP_DIR}/helix-network-setup.sh" ]] && source "${SETUP_DIR}/helix-network-setup.sh" || true

# -------------------------------------------------------------
# Color / CI detection
# -------------------------------------------------------------
COLOR_ENABLED=true
for a in "$@"; do [[ "$a" == "--no-color" ]] && COLOR_ENABLED=false; done
if [[ "${CI:-false}" == "true" ]] || [[ "$(ci_mode_detect 2>/dev/null || echo false)" == "true" ]]; then
  COLOR_ENABLED=false
fi

if [[ "$COLOR_ENABLED" == "false" ]]; then
  RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; BOLD=""; NC=""
else
  RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'
  BLUE=$'\033[0;36m'; CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; NC=$'\033[0m'
fi

OK="${GREEN}✅${NC}"
FAIL="${RED}❌${NC}"
WARN="${YELLOW}⚠️${NC}"
INFO="${BLUE}ℹ️${NC}"

# -------------------------------------------------------------
# Terminal safety
# -------------------------------------------------------------
trap 'tput cnorm; stty sane >/dev/null 2>&1 || true; clear' INT EXIT

# -------------------------------------------------------------
# Simple checks: docker & gum
# -------------------------------------------------------------
require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo -e "${FAIL} 📛️ Docker CLI not installed. Please install docker.${NC}"
    return 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo -e "${FAIL} 📛️ Docker daemon not running or permission denied.${NC}"
    return 1
  fi
  return 0
}

require_gum() {
  if ! command -v gum >/dev/null 2>&1; then
    echo -e "${WARN} ⁉️ gum not found — menu UI will fallback to plain text choices.${NC}"
    return 1
  fi
  return 0
}

# fail early if no docker
require_docker || { echo -e "${FAIL} 📛️ Aborting: Docker required.${NC}"; exit 1; }

# -------------------------------------------------------------
# Safe wrappers and fallbacks (so TUI never dies on stray docker errors)
# -------------------------------------------------------------
run_cmd() {
  local cmd="$*"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} → $cmd"
  else
    eval "$cmd"
  fi
}

docker_safe() {
  docker "$@" 2>/dev/null || true
}

docker_quiet() {
  docker "$@" >/dev/null 2>&1 || true
}

# -------------------------------------------------------------
# If network/volume helpers didn't come from sourced file, provide minimal impl
# -------------------------------------------------------------
create_network_if_not_exists() {
  local network="$1"
  if docker network inspect "$network" >/dev/null 2>&1; then
    printf "%b ⏩️ Network '%s' already exists.\\n" "${OK}" "$network"
    return 0
  fi
  docker network create "$network" >/dev/null 2>&1 && printf "%b Created network '%s'.\\n" "${OK}" "$network" || {
    printf "%b ⁉️ Failed to create network '%s' (maybe exists).\\n" "${WARN}" "$network"
    return 1
  }
}

create_volume_if_not_exists() {
  local vol="$1"
  if docker volume inspect "$vol" >/dev/null 2>&1; then
    printf "%b Volume '%s' already exists.\\n" "${OK}" "$vol"
    return 0
  fi
  docker volume create "$vol" >/dev/null 2>&1 && printf "%b Created volume '%s'.\\n" "${OK}" "$vol" || {
    printf "%b ⁉️ Failed to create volume '%s'.\\n" "${WARN}" "$vol"
    return 1
  }
}

build_image_if_not_exists() {
  local image_tag="${1:-}"
  local dockerfile_path="${2:-}"
  local context="${3:-.}"
  if [[ -z "$image_tag" || -z "$dockerfile_path" ]]; then
    printf "%b ⏩️ build_image_if_not_exists: missing args\\n" "${WARN}"
    return 1
  fi
  if docker images -q "$image_tag" >/dev/null 2>&1 && [[ -n "$(docker images -q "$image_tag")" ]]; then
    printf "%b ⏩️ Image '%s' exists locally.\\n" "${OK}" "$image_tag"
    return 0
  fi
  printf "%b ⏩️ Building image '%s' from %s ...\\n" "${INFO}" "$image_tag" "$dockerfile_path"
  docker build -t "$image_tag" -f "$dockerfile_path" "$context"
  return $?
}

# -------------------------------------------------------------
# Wait for container to be healthy (respect container healthcheck)
# -------------------------------------------------------------
wait_for_container_healthy() {
  local name="$1"
  local timeout="${2:-120}"   # seconds
  local elapsed=0
  local sleep_for=2

  if ! docker ps -a --format '{{.Names}}' | grep -xq "$name"; then
    printf "%b ⁉️ Container '%s' not found.\\n" "${WARN}" "$name"
    return 2
  fi

  while [[ $elapsed -lt $timeout ]]; do
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$name" 2>/dev/null || echo "unknown")
    case "$status" in
      healthy) printf "%b %s is healthy.\\n" "${OK}" "$name"; return 0 ;;
      starting|starting\ *|starting*) printf "%b %s is starting... (%ss)\\n" "${INFO}" "$name" "$elapsed" ;;
      unhealthy) printf "%b %s is unhealthy 📛️ \\n" "${FAIL}" "$name"; return 3 ;;
      Up*|running|running*) printf "%b %s is running (no healthcheck).\\n" "${OK}" "$name"; return 0 ;;
      *)
        printf "%b %s status: %s\\n" "${INFO}" "$name" "$status" ;;
    esac
    sleep "$sleep_for"
    elapsed=$((elapsed + sleep_for))
  done

  printf "%b ⁉️ Timeout waiting for '%s' to become healthy after %ss.\\n" "${WARN}" "$name" "$timeout"
  return 4
}

# -------------------------------------------------------------
# gum-safe helpers (prevent ANSI escaping being passed to gum)
# -------------------------------------------------------------
gum_safe() {
  if command -v gum >/dev/null 2>&1; then
    (unset RED GREEN YELLOW BLUE CYAN BOLD NC; gum "$@")
  else
    # fallback to simple select
    PS3="Choose an option: "
    select opt in "$@"; do
      if [[ -n "$opt" ]]; then
        echo "$opt"
        return 0
      fi
    done
  fi
}

gum_spin_safe() {
  local title="${1:-Working...}"
  local sec="${2:-2}"
  if command -v gum >/dev/null 2>&1; then
    (unset RED GREEN YELLOW BLUE CYAN BOLD NC; gum spin --spinner dot --title "$title" -- sleep "$sec")
  else
    printf "%b %s\\n" "${INFO}" "$title"
    sleep "$sec"
  fi
}

# -------------------------------------------------------------
# Header / dashboard
# -------------------------------------------------------------
draw_header() {
  printf "%s\n" "${CYAN}══════════════════════════════════════════════════════════${NC}"
  printf "  %sHelixNet Control Center%s   %s%s%s\n" "${BLUE}" "${NC}" "${YELLOW}" "${HX_PROJECT_APP_VERSION:-N/A}" "${NC}"
  printf "%s\n" "${CYAN}══════════════════════════════════════════════════════════${NC}"
}

live_dashboard_once() {
  draw_header
  echo ""
  CPU=$(top -bn1 | awk '/Cpu\(s\)/ {print $2 + $4"%"}' || echo "n/a")
  MEM=$(free -h | awk '/Mem:/ {print $3 "/" $2}' || echo "n/a")
  UPT=$(uptime -p | sed 's/up //' || echo "n/a")

  echo -e "🧠 CPU: ${YELLOW}${CPU}${NC} | 💾 RAM: ${YELLOW}${MEM}${NC} | ⏱ ${YELLOW}${UPT}${NC}"
  echo ""
  echo -e "${BLUE}Containers:${NC}"
  local services=(traefik ollama openwebui qdrant postgres rabbitmq redis helix helix-worker helix-beat)
  for s in "${services[@]}"; do
    st=$(docker_safe ps --filter "name=^/${s}$" --format '{{.Status}}' || echo "")
    [[ -z "$st" ]] && st="not present"
    echo "  ${s}: ${st}"
  done
  echo ""
  echo -e "${BLUE}Quick Links:${NC}"
  echo "  API Docs: https://helix-platform.local/docs"
  echo "  Grafana:  https://grafana.helix.local"
  echo ""
}

live_dashboard_loop() {
  local delay="${1:-10}"
  trap 'tput cnorm; exit' SIGINT SIGTERM
  tput civis || true
  while true; do
    clear
    live_dashboard_once
    gum_spin_safe "Refreshing..." "$delay"
  done
}
select_model_runtime() {
  echo -e "${INFO} Fetching installed models...${NC}"

  local models
  models=$(ollama list 2>/dev/null | awk 'NR>1 {print $1}')

  if [[ -z "$models" ]]; then
    echo -e "${WARN} No models installed yet. Pull one first.${NC}"
    return
  fi

  selected_model=$(printf "%s\n" "$models" | gum choose --header="Select runtime model")

  if [[ -z "$selected_model" ]]; then
    echo -e "${WARN} No model selected.${NC}"
    return
  fi

  # Assuming this path is correct for model selection storage
  echo "$selected_model" > /var/tmp/helix_ollama_model
  echo -e "${OK} Selected model saved: $selected_model${NC}"

  # Restart the debllm worker if present
  docker ps -q -f name=debllm >/dev/null && docker restart debllm || true
}

# -------------------------------------------------------------
# AI menu (safe: only restart when necessary)
# -------------------------------------------------------------
ai_menu() {
  # Define the compose file variables for clarity, assuming boot flow uses them
  local core_comp="${ROOT_DIR}/compose/helix-core/core-stack.yml"
  local llm_comp="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"
  
  while true; do
    clear
    echo -e "${YELLOW}🤖 AI / OLLAMA MENU${NC}"
    choice=$(gum_safe choose \
      "Start Ollama services" \
      "List available models" \
      "Pull new model" \
      "Select model for runtime" \
      "Back")
    case "$choice" in
      "Start Ollama services")
        # Ensure core services are up before starting LLM stack dependencies
        echo -e "${INFO} Checking if core stack is running...${NC}"
        run_cmd docker compose -f "$core_comp" up -d --build --remove-orphans 2>/dev/null || true

        run_cmd docker compose -f "$llm_comp" up -d --build --remove-orphans
        gum_spin_safe "Starting Ollama stack..." 3
        wait_for_container_healthy "ollama" 120 || echo -e "${WARN} ⁉️ ollama health check not green yet${NC}"
        ;;
      "List available models")
        "${MODULES_DIR}/helix-ollama.sh" list || echo -e "${WARN} ⁉️ Could not list models (helper returned non-zero)${NC}"
        ;;
      "Pull new model")
        "${MODULES_DIR}/helix-ollama.sh" pull || echo -e "${WARN} ⁉️ Pull may have failed${NC}"
        # If a model was pulled we should restart the debllm worker if present
        if docker ps -q -f name=debllm >/dev/null 2>&1; then
          echo -e "${INFO} Restarting debllm to pick up new model...${NC}"
          docker restart debllm 2>/dev/null || true
        fi
        ;;
      "Select model for runtime") select_model_runtime ;;

      "Back") return ;;
    esac
    gum_spin_safe "Returning..." 1
  done
}

# -------------------------------------------------------------
# Cleanup menu (Updated to use the new helix-reset-cleaner.sh)
# -------------------------------------------------------------
cleanup_menu() {
  while true; do
    clear
    echo -e "${RED}🧹 Docker Cleanup Menu${NC}"
    choice=$(gum_safe choose \
      "Run full Safe Cleanup (Stop all stacks & Prune volumes)" \
      "Back")
    case "$choice" in
      "Run full Safe Cleanup (Stop all stacks & Prune volumes)")
        # Now calls the single, fixed, powerful cleanup script
        "${MODULES_DIR}/helix-reset-cleaner.sh"
        ;;
      "Back") return ;;
    esac
    gum_spin_safe "Returning..." 1
  done
}

# -------------------------------------------------------------
# Boot flow with basic health waits (Core -> Main -> LLM)
# -------------------------------------------------------------
run_boot_flow() {
  local core_comp="${ROOT_DIR}/compose/helix-core/core-stack.yml"
  local main_comp="${ROOT_DIR}/compose/helix-main/main-stack.yml"
  local llm_comp="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"

  clear
  echo -e "${GREEN}🛠️ Helix Boot${NC}   (dry-run: $DRY_RUN)"

  # Stage A: Core
  if [[ "$ONLY_MAIN" == "false" && "$ONLY_LLM" == "false" ]]; then
    echo -e "\n${INFO} Stage 🅰 Core${NC}"
    run_cmd docker compose -f "$core_comp" up -d --build --remove-orphans
    [[ "$DRY_RUN" == "false" ]] && wait_for_container_healthy "postgres" 120
  else
    echo -e "${INFO} Skipping Core stage (flag)${NC}"
  fi

  # Stage B: Main
  if [[ "$ONLY_CORE" == "false" && "$ONLY_LLM" == "false" ]]; then
    echo -e "\n${INFO} Stage 🅱 Main${NC}"
    run_cmd docker compose -f "$main_comp" up -d --build --remove-orphans
    [[ "$DRY_RUN" == "false" ]] && wait_for_container_healthy "helix" 120
  else
    echo -e "${INFO} Skipping Main stage (flag)${NC}"
  fi

  # Stage C: LLM
  if [[ "$ONLY_CORE" == "false" && "$ONLY_MAIN" == "false" ]]; then
    echo -e "\n${INFO} Stage 🦜 LLM${NC}"
    run_cmd docker compose -f "$llm_comp" up -d --build --remove-orphans
    [[ "$DRY_RUN" == "false" ]] && wait_for_container_healthy "llm" 120
  else
    echo -e "${INFO} Skipping LLM stage (flag)${NC}"
  fi

  echo -e "\n${OK} Boot complete.${NC}"
}

# -------------------------------------------------------------
# Stop / teardown helper (clean reverse order, uses fixed paths)
# -------------------------------------------------------------
stop_all() {
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-llm/llm-stack.yml" down --remove-orphans 2>/dev/null || true
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-main/main-stack.yml" down --remove-orphans 2>/dev/null || true
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-core/core-stack.yml" down --remove-orphans 2>/dev/null || true
  gum_spin_safe "Stopped." 1
}

# -------------------------------------------------------------
# Main menu (Updated to use descriptive, user-preferred labels)
# -------------------------------------------------------------
show_main_menu() {
  while true; do
    clear
    draw_header
    echo -e "Host: $(hostname) | Docker: $(docker -v 2>/dev/null | cut -d',' -f1 || echo 'n/a')"
    echo ""
    choice=$(gum_safe choose \
      "🚀 Start Helix Platform" \
      "📊 Platform Status" \
      "Live Dashboard (once)" \
      "Live Dashboard (auto-refresh 10s)" \
      "Run diagnostics" \
      "🤖 AI Model Center" \
      "🧹 Reset Demo" \
      "Stop Helix stack" \
      "Quit")
    case "$choice" in
      "🚀 Start Helix Platform") run_boot_flow ;;
      "📊 Platform Status") "${MODULES_DIR}/helix-status-v2.sh" ;; # Calls the status script
      "Live Dashboard (once)") clear; live_dashboard_once; gum_spin_safe "Back..." 2 ;;
      "Live Dashboard (auto-refresh 10s)") live_dashboard_loop 10 ;;
      "Run diagnostics") "${MODULES_DIR}/helix-diagnostics.sh" --no-color || echo -e "${WARN} Diagnostics error${NC}" ;;
      "🤖 AI Model Center") ai_menu ;;
      "🧹 Reset Demo") cleanup_menu ;; # Calls the cleanup menu, which now uses the fixed script
      "Stop Helix stack") stop_all ;;
      "Quit") echo -e "${GREEN}👋 Exiting...${NC}"; exit 0 ;;
      *) echo -e "${WARN} ⁉️ Unknown choice${NC}" ;;
    esac
  done
}

# -------------------------------------------------------------
# STARTUP: Create networks, volumes, base image — THEN menu
# -------------------------------------------------------------
echo -e "${BLUE} ⚓️ Creating Helix Docker networks...${NC}"
create_network_if_not_exists "helixnet_core"
create_network_if_not_exists "helixnet_edge"
echo -e "${GREEN}Network setup complete.${NC}"

echo -e "${BLUE} 🐬️ Ensuring core volumes exist...${NC}"
create_volume_if_not_exists "postgres_data"
create_volume_if_not_exists "redis_data"
create_volume_if_not_exists "minio_data"
create_volume_if_not_exists "grafana_data"
create_volume_if_not_exists "prometheus_data"
create_volume_if_not_exists "keycloak_data"
create_volume_if_not_exists "portainer_data"
create_volume_if_not_exists "vault_data"
echo -e "${GREEN}Volume setup complete.${NC}"

echo -e "\n${BLUE} 👀 Checking & building helix-base image (if needed)...${NC}"
build_image_if_not_exists "helix-base" "compose/helix-main/Dockerfile.base" "."
echo -e "${GREEN}Image setup complete.${NC}"

# Finally show the menu
show_main_menu