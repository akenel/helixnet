#!/usr/bin/env bash
# scripts/tools/helix-utils.sh
# Shared utilities: .env loader, banner, gum-safe wrapper, docker helpers.
set -euo pipefail
IFS=$'\n\t'

# -----------------------------------------------------------------------------
# Basic color defaults (can be disabled by --ci / --no-color)
# exported here only if required by callers (avoid exporting BOLD/gum envs)
# -----------------------------------------------------------------------------
BLUE=${BLUE:-$'\033[0;36m'}
CYAN=${CYAN:-$'\033[0;36m'}
GREEN=${GREEN:-$'\033[0;32m'}
YELLOW=${YELLOW:-$'\033[0;33m'}
RED=${RED:-$'\033[0;31m'}
NC=${NC:-$'\033[0m'}
BOLD=${BOLD:-$'\033[1m'}

# Flag (off by default) — set to "true" in CI or when --no-gum passed
CI_MODE=${CI_MODE:-false}
NO_GUM=${NO_GUM:-false}
NO_COLOR=${NO_COLOR:-false}

# simple die helper
die() { echo -e "${RED}FATAL:${NC} $*"; exit 1; }

# load .env safely (does not export if not desired)
load_env() {
  local envfile="${1:-.env}"
  if [[ -f "$envfile" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$envfile"
    set +a
    echo "ℹ️  Loaded environment from $envfile"
  else
    echo "⚠️  No .env at $envfile"
  fi
}

# -----------------------------------------------------------------------------
# CI / no-color helpers
# -----------------------------------------------------------------------------
disable_colors() {
  NO_COLOR=true
  BLUE=''; CYAN=''; GREEN=''; YELLOW=''; RED=''; NC=''
  BOLD=''
  export NO_COLOR
}

enable_colors() {
  NO_COLOR=false
  BLUE=${BLUE:-$'\033[0;36m'}
  CYAN=${CYAN:-$'\033[0;36m'}
  GREEN=${GREEN:-$'\033[0;32m'}
  YELLOW=${YELLOW:-$'\033[0;33m'}
  RED=${RED:-$'\033[0;31m'}
  NC=${NC:-$'\033[0m'}
  BOLD=${BOLD:-$'\033[1m'}
  export NO_COLOR
}

set_ci_mode() {
  CI_MODE=true
  NO_GUM=true
  disable_colors
  export CI_MODE NO_GUM NO_COLOR
}

# banner - use your assets/helix-banner.txt if available
banner_show() {
  local BANNER_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/assets/helix-banner.txt"
  if [[ -f "$BANNER_FILE" ]]; then
    echo -e "${CYAN}"
    cat "$BANNER_FILE"
    echo -e "${NC}"
  else
    echo -e "${CYAN}=== HELIX ===${NC}"
  fi
}
debllm_events() {
  # in scripts/modules/helix-dashboard.sh or a new module
  psql "$POSTGRES_DSN" -At -c "SELECT id, container, left(summary,200) FROM debllm_events WHERE status='new' ORDER BY created_at DESC LIMIT 20;"
# toDo >>> add the minio open the raw logs  with mc cp and mc cat <<<

}

# gum-safe spinner wrapper: temporarily unset BOLD to avoid gum parsing problems
gum_spin_safe() {
  local secs="${1:-5}"
  local title="${2:-waiting...}"

  if [[ "$CI_MODE" == "true" || "$NO_GUM" == "true" ]]; then
    # CI mode -> no gum UI; produce compact progress dots
    printf "%s " "$title"
    for i in $(seq 1 "$secs"); do printf "."; sleep 1; done
    printf "\n"
    return 0
  fi

  # save BOLD and GUM envs which gum may parse incorrectly
  local _BOLD_SAVE="${BOLD-}"
  local _GUM_BOLD_SAVE="${GUM_BOLD-}"

  unset BOLD
  unset GUM_BOLD

  if command -v gum &>/dev/null; then
    gum spin --spinner dot --title "$title" -- sleep "$secs"
  else
    printf "%s " "$title"
    for i in $(seq 1 "$secs"); do printf "."; sleep 1; done
    printf "\n"
  fi

  # restore
  [[ -n "$_BOLD_SAVE" ]] && BOLD="$_BOLD_SAVE"
  [[ -n "$_GUM_BOLD_SAVE" ]] && GUM_BOLD="$_GUM_BOLD_SAVE"
}

# check docker available
require_docker() {
  if ! command -v docker &>/dev/null; then
    echo "❌ docker not found - please install/run docker"
    return 1
  fi
  docker info >/dev/null 2>&1 || { echo "❌ docker daemon not running or not accessible"; return 1; }
  return 0
}

# create network if missing
create_network_if_not_exists() {
  local net="$1"
  if ! docker network inspect "$net" >/dev/null 2>&1; then
    echo "🔧 Creating docker network: $net"
    docker network create "$net" >/dev/null
  else
    echo "ℹ️  Docker network exists: $net"
  fi
}

# safer docker-compose file locator: try given path, fallback to old names
find_compose_file() {

  local base="compose/helix-core"
  local main="${base}/core-stack.yml"
  local fallback1="${base}/docker-compose.yml"
  local fallback2="docker-compose.yml"
  local fallback3="compose.yml"

  echo "🔎 Searching for compose file..."

  for candidate in "$main" "$fallback1" "$fallback2" "$fallback3"; do
    if [[ -f "$candidate" ]]; then
      COMPOSE_FILE="$candidate"
      echo "📦 Using compose file: $COMPOSE_FILE"
      return 0
    fi
  done

  die "❌ No usable Docker Compose file found in:
  - $main
  - $fallback1
  - $fallback2
  - $fallback3
  📍 Fix your layout or create one."
}


# wait-for-container healthy (timeout seconds)
wait_for_service_healthy() {
  local name="$1"
  local timeout="${2:-60}"
  local waited=0
  while [ $waited -lt "$timeout" ]; do
    local state
    state=$(docker inspect -f '{{.State.Health.Status}}' "$name" 2>/dev/null || echo "no-health")
    if [[ "$state" == "healthy" ]]; then
      echo "✅ $name healthy"
      return 0
    fi
    if docker ps --filter "name=^/${name}$" --format '{{.Names}}' | grep -q "$name"; then
      echo -n "."
    else
      echo "⚠️  $name not running yet"
    fi
    sleep 2
    waited=$((waited+2))
  done
  echo ""
  echo "❌ $name did not become healthy within ${timeout}s"
  return 1
}

# ------------------------------------------------------------------------------
# 🕒 Timer helpers
# ------------------------------------------------------------------------------
start_timer() { 
  _start_time=$(date +%s)
}

end_timer() {
  local end=$(date +%s)
  local duration=$((end - _start_time))
  echo -e "${CYAN}⏱️ Runtime: ${duration}s${NC}"
}

# ------------------------------------------------------------------------------
# 🌐 Safe curl wrapper (always returns HTTP status or “000”)
# ------------------------------------------------------------------------------
safe_curl_status() {
  local url="$1"
  curl -sk -o /dev/null -w "%{http_code}" --max-time 4 "$url" 2>/dev/null || echo "000"
}

# ------------------------------------------------------------------------------
# 🧹 ANSI color stripper (for CI logs or text parsing)
# ------------------------------------------------------------------------------
strip_ansi() { 
  sed 's/\x1B\[[0-9;]*[JKmsu]//g'
}

# ------------------------------------------------------------------------------
# 📊 Memory & Disk Usage helpers
# ------------------------------------------------------------------------------
system_memory_gb() {
  free -g | awk '/Mem:/ {print $2}'
}

disk_usage_summary() {
  df -h --output=source,size,used,avail,pcent,target | grep -E '^Filesystem|/$|^/home|^/var|^/opt'
}

# ------------------------------------------------------------------------------
# 🧰 Dependency check helper (prints to stdout)
# ------------------------------------------------------------------------------
check_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo -e "${RED}❌ Missing required tool: ${cmd}${NC}"
    return 1
  }
  return 0
}

# ------------------------------------------------------------------------------
# 🧩 Print section headers
# ------------------------------------------------------------------------------
print_header() {
  local title="$1"
  printf "\n${CYAN}════════════════════════════════════════════════════════════════${NC}\n"
  printf "${BOLD}${CYAN}%s${NC}\n" "$title"
  printf "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"
}

# ------------------------------------------------------------------------------
# 🧠 Human-readable summary generator
# ------------------------------------------------------------------------------
summarize_health() {
  local healthy="$1"
  local degraded="$2"
  echo -e "${GREEN}Healthy: ${healthy}${NC} | ${YELLOW}Degraded: ${degraded}${NC}"
}

# ------------------------------------------------------------------------------
# 🪪 CI Mode detector (true if running under GitHub/GitLab/Jenkins)
# ------------------------------------------------------------------------------
ci_mode_detect() {
  if [[ -n "${CI:-}" || -n "${GITHUB_ACTIONS:-}" || -n "${GITLAB_CI:-}" ]]; then
    echo "true"
  else
    echo "false"
  fi
}
# ------------------------------------------------------------------------------
# 🪪 load the environement vars from the /ENV root folder files  
# ------------------------------------------------------------------------------
load_env_file() {
    for f in ".env" "env/helix.env"; do
        if [[ -f "$f" ]]; then
            echo "🔧 Loading environment from $f"
            set -a
            source "$f"
            set +a
        fi
    done
}