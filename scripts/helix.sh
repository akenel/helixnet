#!/usr/bin/env bash
# =============================================================
# 🧭 HelixNet Control Center - Interactive TUI (v5 SHERLOCK)
# =============================================================
# - Polished: networks -> volumes -> image -> menu
# - Gum-safe, Docker-safe, idempotent
# - Smart Auto dependency resolver (KIC / KIS style)
# =============================================================
set -e

REQUIRED_NETWORKS=("helixnet_core" "helixnet_edge")

echo "🔹 Checking required networks..."

for net in "${REQUIRED_NETWORKS[@]}"; do
    if docker network ls --format '{{.Name}}' | grep -qw "$net"; then
        echo "✅ Network exists: $net"
    else
        echo "⚠️  Missing: $net — creating..."
        docker network create "$net"
        echo "✨ Created: $net"
    fi
done

set -o errexit
set -o nounset
set -o pipefail
IFS=$'\n\t'

# ------------------------------------------------------------------
# Basic config: networks that must exist before compose up (tweak if needed)
# ------------------------------------------------------------------
REQUIRED_NETWORKS=( "helixnet_core" "helixnet_edge" )

# ------------------------------------------------------------------
# Simple log helpers (emoji-prefixed, silent-mode for bells)
# ------------------------------------------------------------------
info()  { printf "%b %s\n" "ℹ️" " $*"; }
ok()    { printf "%b %s\n" "✅" " $*"; }
warn()  { printf "%b %s\n" "⚠️" " $*"; }
fail()  { printf "%b %s\n" "❌" " $*"; }

# ------------------------------------------------------------------
# CLI Flags
# ------------------------------------------------------------------
DRY_RUN=false
ONLY_CORE=false
ONLY_MAIN=false
ONLY_LLM=false

# parse args properly
for arg in "$@"; do
  case "$arg" in
    --help)
      cat <<EOF
Helix Control Center Flags
  --dry-run     Show docker commands without running them
  --only-core   Boot only: DB, Traefik, Keycloak, Redis, Postgres
  --only-main   Boot only: API stack (auto-starts core if missing)
  --only-llm    Boot only: Ollama + LLM stack (auto-starts core+main if missing)
EOF
      exit 0
      ;;
    --dry-run) DRY_RUN=true ;;
    --only-core) ONLY_CORE=true ;;
    --only-main) ONLY_MAIN=true ;;
    --only-llm) ONLY_LLM=true ;;
  esac
done

# ------------------------------------------------------------------
# Resolve repo paths
# ------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="${ROOT_DIR}/scripts/tools"
MODULES_DIR="${ROOT_DIR}/scripts/modules"
SETUP_DIR="${MODULES_DIR}/setup"

# ------------------------------------------------------------------
# Load helpers if available (non-fatal)
# ------------------------------------------------------------------
[[ -f "${TOOLS_DIR}/helix-utils.sh" ]] && source "${TOOLS_DIR}/helix-utils.sh" || true
[[ -f "${TOOLS_DIR}/helix-common.sh" ]] && source "${TOOLS_DIR}/helix-common.sh" || true
[[ -f "${TOOLS_DIR}/sys-checks.sh" ]] && source "${TOOLS_DIR}/sys-checks.sh" || true
[[ -f "${SETUP_DIR}/helix-network-setup.sh" ]] && source "${SETUP_DIR}/helix-network-setup.sh" || true

# ------------------------------------------------------------------
# Detect terminal hyperlink support (non-fatal)
# ------------------------------------------------------------------
if [[ -z "${TERM_PROGRAM:-}" && -z "${WT_SESSION:-}" ]]; then
  warn "Terminal hyperlink support unknown — links may not be clickable."
fi

# ------------------------------------------------------------------
# Color / CI detection
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Terminal safety
# ------------------------------------------------------------------
trap 'tput cnorm; stty sane >/dev/null 2>&1 || true; clear' INT EXIT

# ------------------------------------------------------------------
# Simple checks: docker & gum
# ------------------------------------------------------------------
require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker CLI not installed. Please install docker."
    return 1
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker daemon not running or permission denied."
    return 1
  fi
  return 0
}

require_gum() {
  if ! command -v gum >/dev/null 2>&1; then
    warn "gum not found — menu UI will fallback to plain text choices."
    return 1
  fi
  return 0
}

# fail early if no docker
require_docker || { fail "Aborting: Docker required."; exit 1; }

# ------------------------------------------------------------------
# Safe wrappers and fallbacks (so TUI never dies on stray docker errors)
# ------------------------------------------------------------------
# run_cmd: in dry-run mode prints the command, else runs it and preserves exit code
run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    printf "%b %s\n" "${YELLOW}[DRY-RUN]${NC}" "→ $*"
    return 0
  fi
  eval "$@"
  return $?
}

docker_safe() {
  docker "$@" 2>/dev/null || true
}
docker_quiet() {
  docker "$@" >/dev/null 2>&1 || true
}

# ------------------------------------------------------------------
# Networks: ensure required networks exist (prevents second-run failures)
# ------------------------------------------------------------------
create_network_if_not_exists() {
  local network="$1"
  if docker network inspect "$network" >/dev/null 2>&1; then
    ok "Network '${network}' already exists."
    return 0
  fi

  run_cmd docker network create "$network" >/dev/null 2>&1 \
    && ok "Created network '${network}'." \
    || warn "Failed to create network '${network}' (it may already exist or require privileges)."
}

ensure_network() {
  local net="$1"

  if ! docker network ls --format '{{.Name}}' | grep -q "^${net}$"; then
    echo "🌐 Creating network: $net"
    docker network create "$net" >/dev/null 2>&1 || {
      echo "❌ Failed to create network $net"
      exit 1
    }
  else
    echo "🌐 Network OK: $net"
  fi
}
ensure_all_networks() {
  ensure_network "helixnet_core"
  ensure_network "helixnet_edge"
}
# ------------------------------------------------------------------
# Volumes: create if missing (idempotent)
# ------------------------------------------------------------------
create_volume_if_not_exists() {
  local vol="$1"
  if docker volume inspect "$vol" >/dev/null 2>&1; then
    ok "Volume '$vol' already exists."
    return 0
  fi
  run_cmd docker volume create "$vol" >/dev/null 2>&1 \
    && ok "Created volume '$vol'." \
    || warn "Failed to create volume '$vol'."
}

# ------------------------------------------------------------------
# build image if missing
# ------------------------------------------------------------------
build_image_if_not_exists() {
  local image_tag="${1:-}"
  local dockerfile_path="${2:-}"
  local context="${3:-.}"
  if [[ -z "$image_tag" || -z "$dockerfile_path" ]]; then
    warn "build_image_if_not_exists: missing args"
    return 1
  fi
  if docker images -q "$image_tag" >/dev/null 2>&1 && [[ -n "$(docker images -q "$image_tag")" ]]; then
    ok "Image '$image_tag' exists locally."
    return 0
  fi
  info "Building image '$image_tag' from $dockerfile_path ..."
  run_cmd docker build -t "$image_tag" -f "$dockerfile_path" "$context"
  return $?
}

# ------------------------------------------------------------------
# Health wait with skip for containers without healthcheck
# ------------------------------------------------------------------
wait_for_container_healthy() {
  local name="$1"
  local timeout="${2:-120}"
  local elapsed=0
  local sleep_for=2

  if ! docker ps -a --format '{{.Names}}' | grep -xq "$name"; then
    warn "Container '$name' not found."
    return 2
  fi

  # detect if the container has health information
  has_health=$(docker inspect --format '{{if .State.Health}}yes{{else}}no{{end}}' "$name" 2>/dev/null || echo "no")
  if [[ "$has_health" != "yes" ]]; then
    # no formal healthcheck — treat "Up" as OK, but we still test for running state
    for ((elapsed=0; elapsed<timeout; elapsed+=sleep_for)); do
      state=$(docker inspect --format '{{.State.Status}}' "$name" 2>/dev/null || echo "unknown")
      if [[ "$state" == "running" ]]; then
        ok "$name is running (no healthcheck)."
        return 0
      fi
      sleep "$sleep_for"
    done
    warn "Timeout waiting for '$name' to start (no healthcheck)."
    return 4
  fi

  # If container has healthcheck, respect it
  while [[ $elapsed -lt $timeout ]]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "unknown")
    case "$status" in
      healthy) ok "$name is healthy."; return 0 ;;
      starting*) info "$name is starting... (${elapsed}s)" ;;
      unhealthy) fail "$name is unhealthy."; return 3 ;;
      *) info "$name status: $status" ;;
    esac
    sleep "$sleep_for"
    elapsed=$((elapsed + sleep_for))
  done

  warn "Timeout waiting for '$name' to become healthy after ${timeout}s."
  return 4
}

# ------------------------------------------------------------------
# gum wrappers (unchanged but tidy)
# ------------------------------------------------------------------
gum_safe() {
  if command -v gum >/dev/null 2>&1; then
    (unset RED GREEN YELLOW BLUE CYAN BOLD NC; gum "$@")
  else
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
    info "$title"
    sleep "$sec"
  fi
}

# ------------------------------------------------------------------
# Header / dashboard
# ------------------------------------------------------------------
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
  local services=(traefik ollama openwebui qdrant postgres rabbitmq redis helix worker beat)
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

# ------------------------------------------------------------------
# Model selector (polished and safe)
# ------------------------------------------------------------------
select_model_runtime() {
  info "Fetching installed models..."
  local models
  models=$(ollama list 2>/dev/null | awk 'NR>1 {print $1}' || true)

  if [[ -z "$models" ]]; then
    warn "No models installed yet. Pull one first."
    return
  fi

  selected_model=$(printf "%s\n" "$models" | gum choose --header="Select runtime model" 2>/dev/null || true)

  if [[ -z "$selected_model" ]]; then
    warn "No model selected."
    return
  fi

  run_cmd bash -c "echo '$selected_model' > /var/tmp/helix_ollama_model"
  ok "Selected model saved: $selected_model"

  docker ps -q -f name=debllm >/dev/null && docker restart debllm || true
}

# ------------------------------------------------------------------
# AI menu
# ------------------------------------------------------------------
ai_menu() {
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
        info "Ensuring required networks..."
        ensure_networks
        info "Starting Ollama stack (will auto-start core if needed)..."
        # Smart-auto: ensure core exists before LLMs
        if ! docker ps --filter "name=^/postgres$" --format '{{.Names}}' | grep -q "postgres"; then
          info "Core seems missing — starting core first..."
          run_cmd docker compose -f "$core_comp" up -d --build --remove-orphans
          [[ "$DRY_RUN" == "false" ]] && wait_for_container_healthy "postgres" 120 || true
        fi

        run_cmd docker compose -f "$llm_comp" up -d --build --remove-orphans
        gum_spin_safe "Starting Ollama stack..." 3
        [[ "$DRY_RUN" == "false" ]] && wait_for_container_healthy "ollama" 120 || warn "Ollama health not green yet."
        ;;
      "List available models")
        "${MODULES_DIR}/helix-ollama.sh" list || warn "Could not list models (helper returned non-zero)"
        ;;
      "Pull new model")
        "${MODULES_DIR}/helix-ollama.sh" pull || warn "Pull may have failed"
        docker ps -q -f name=debllm >/dev/null 2>&1 && docker restart debllm || true
        ;;
      "Select model for runtime") select_model_runtime ;;
      "Back") return ;;
    esac
    gum_spin_safe "Returning..." 1
  done
}

# ------------------------------------------------------------------
# Cleanup menu (safe)
# ------------------------------------------------------------------
cleanup_menu() {
  while true; do
    clear
    echo -e "${RED}🧹 Docker Cleanup Menu${NC}"
    choice=$(gum_safe choose \
      "Run full Safe Cleanup (Stop all stacks & Prune volumes - safe)" \
      "Back")
    case "$choice" in
      "Run full Safe Cleanup (Stop all stacks & Prune volumes - safe)")
        if [[ -x "${MODULES_DIR}/helix-reset-cleaner.sh" ]]; then
          info "Running safe cleanup..."
          "${MODULES_DIR}/helix-reset-cleaner.sh"
        else
          warn "Cleanup script not found: ${MODULES_DIR}/helix-reset-cleaner.sh"
        fi
        ;;
      "Back") return ;;
    esac
    gum_spin_safe "Returning..." 1
  done
}

# ------------------------------------------------------------------
# Boot flow (smart-auto): ensures networks/volumes/images and auto-starts deps
# ------------------------------------------------------------------
run_boot_flow() {
  clear
  info "🚀 Smart Boot Sequence (Auto-Resolve Mode)"

  ensure_all_networks

  local core="${ROOT_DIR}/compose/helix-core/core-stack.yml"
  local main="${ROOT_DIR}/compose/helix-main/main-stack.yml"
  local llm="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"

  # CORE
  info "🅰 Starting Core…"
  docker compose -f "$core" up -d --build --remove-orphans

  # MAIN (depends on core)
  info "🅱 Starting Main…"
  docker compose -f "$main" up -d --build --remove-orphans

  # LLM (depends on main and core)
  info "🦜 Starting LLM…"
  docker compose -f "$llm" up -d --build --remove-orphans

  success "🏁 Boot Complete — All stacks attempted."
}

# ------------------------------------------------------------------
# Stop / teardown helper (clean reverse order, uses fixed paths)
# ------------------------------------------------------------------
stop_all() {
  info "Stopping LLM..."
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-llm/llm-stack.yml" down --remove-orphans 2>/dev/null || true
  info "Stopping Main..."
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-main/main-stack.yml" down --remove-orphans 2>/dev/null || true
  info "Stopping Core..."
  run_cmd docker compose -f "${ROOT_DIR}/compose/helix-core/core-stack.yml" down --remove-orphans 2>/dev/null || true
  gum_spin_safe "Stopped." 1
}

# ------------------------------------------------------------------
# Main menu
# ------------------------------------------------------------------
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
      "📊 Platform Status") "${MODULES_DIR}/helix-status-v2.sh" ;;
      "Live Dashboard (once)") clear; live_dashboard_once; gum_spin_safe "Back..." 2 ;;
      "Live Dashboard (auto-refresh 10s)") live_dashboard_loop 10 ;;
      "Run diagnostics") "${MODULES_DIR}/helix-diagnostics.sh" --no-color || warn "Diagnostics error" ;;
      "🤖 AI Model Center") ai_menu ;;
      "🧹 Reset Demo") cleanup_menu ;;
      "Stop Helix stack") stop_all ;;
      "Quit") ok "Exiting..."; exit 0 ;;
      *) warn "Unknown choice" ;;
    esac
  done
}

# ------------------------------------------------------------------
# STARTUP: create base networks, volumes, build base image (idempotent), THEN menu
# ------------------------------------------------------------------
info "⚓️ Ensuring Helix Docker networks..."
ensure_networks
ok "Network setup complete."

info "🐬️ Ensuring core volumes exist..."
create_volume_if_not_exists "postgres_data"
create_volume_if_not_exists "redis_data"
create_volume_if_not_exists "minio_data"
create_volume_if_not_exists "grafana_data"
create_volume_if_not_exists "prometheus_data"
create_volume_if_not_exists "keycloak_data"
create_volume_if_not_exists "portainer_data"
create_volume_if_not_exists "vault_data"
ok "Volume setup complete."

info "👀 Checking & building helix-base image (if needed)..."
build_image_if_not_exists "helix-base" "compose/helix-main/Dockerfile.base" "."
ok "Image setup complete."

# Finally show the menu
show_main_menu
