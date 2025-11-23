#!/usr/bin/env bash
# ==========================================================
# 🥋 HelixNet Health Matrix 💚️ ./scripts/helix-health.sh
# ==========================================================
# Author: Angel 🧩 Refactored by Sherlock
# Purpose: Unified system health check for the HelixNet stack
# ----------------------------------------------------------
set -euo pipefail
IFS=$'\n\t'
SECONDS=0
FAIL_COUNT=0

# -----------------------------------------------------------------------------------------------
# ---- Configurable defaults 
# -----------------------------------------------------------------------------------------------

# scripts/tools/helix-common.sh
source "$(dirname "$0")/scripts/tools/helix-common.sh"
banner_show
echo "Direct run ./scripts/helix-health.sh (or via Helix-TUI > Health Check Summary) "
  # gum_spin_safe() 6s "✔️ Booting Helix Matrix"
(unset BOLD RED GREEN YELLOW BLUE CYAN; gum_spin_safe 2 " ✔️ Booting Helix Matrix.")

# ==========================================================
# 📦 ENVIRONMENT LOADING
# ==========================================================
ENV_FILE=".env"
[ ! -f "$ENV_FILE" ] && [ -f "../.env" ] && ENV_FILE="../.env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  set -a; source "$ENV_FILE"; set +a
  echo -e "${INFO} ${GREEN} Configuration loaded from → ${ENV_FILE} ✅ ${NC}"
else
  echo -e "${FAIL} ERROR:${NC} No .env file found!"
fi
# ==========================================================
# 🧠 ENVIRONMENT CONTEXT
# ==========================================================
KEYCLOAK_DEV_REALM="${KEYCLOAK_DEV_REALM:=unknown}"
IN_DOCKER=false
[[ -f /.dockerenv ]] && IN_DOCKER=true

docker_running() { docker info >/dev/null 2>&1; }
if ! docker_running; then
  echo -e "$SKIP Docker not running. Skipping container health checks.${NC}"
  exit 0
fi

compose_up() { docker compose ls 2>/dev/null | grep -q 'helix' || false; }

# ==========================================================
# 🚦 TRAEFIK HOST DETECTION
# ==========================================================
TRAEFIK_HOST=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E 'traefik|reverse-proxy' | head -n 1 || true)
TRAEFIK_DOMAIN="helix.local"

if [[ -n "$TRAEFIK_HOST" ]]; then
  TRAEFIK_RULE=$(docker inspect "$TRAEFIK_HOST" 2>/dev/null | grep -E '"traefik.http.routers.*rule"' | grep -o 'Host(`[^`]*`)' | head -n 1 | cut -d'`' -f2 || true)
  [[ -n "$TRAEFIK_RULE" ]] && TRAEFIK_DOMAIN="$TRAEFIK_RULE"
fi

# ==========================================================
# 🌐 HELPER: HTTP CHECK
# ==========================================================
check_http() {
  local NAME="$1"; local URL="$2"; local EXPECTED="$3"
  local STATUS
  STATUS=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "$URL" || echo "000")

  if [[ "$STATUS" =~ ^2[0-9]{2}$ ]] || [[ "$STATUS" == "$EXPECTED" ]]; then
    echo -e "$OK ${GREEN}OK${NC} $NAME → ${BLUE}$URL${NC} (${STATUS})"
  else
    echo -e "$FAIL ${RED}FAIL${NC} $NAME → ${BLUE}$URL${NC} (${STATUS}, expected $EXPECTED/2xx)"
    ((FAIL_COUNT++))
  fi
}

# ==========================================================
# 🧩 HELPER: INTERNAL PING (Docker network)
# ==========================================================
check_ping() {
  local NAME="$1"; local HOST="$2"
  if command -v docker &>/dev/null; then
    if docker compose ps 2>/dev/null | grep -q "$NAME.*running"; then
      docker run --rm --network "${PROJECT_NAME:-helix}" busybox ping -c1 -W1 "$HOST" >/dev/null 2>&1 \
        && echo -e "$OK ${GREEN}OK${NC} $NAME ($HOST)" \
        || echo -e "$FAIL ${RED}FAIL${NC} $NAME ($HOST)"
    else
      echo -e "$SKIP ${YELLOW}SKIP${NC} $NAME ($HOST) - container not running"
      ((FAIL_COUNT++))
      echo -e "$FAIL ${RED}FAIL${NC} $NAME → ${BLUE}$URL${NC} (${STATUS}, expected $EXPECTED/2xx)"
fi

  else
    echo -e "$SKIP ${YELLOW}Docker CLI unavailable${NC}"
  fi
}

# ==========================================================
# ⚙️ CONFIGURATION MATRIX
# ==========================================================
echo -e "\n${BLUE}--- ⚙️  CONFIGURATION MATRIX ---${NC}"
printf "%-28s | %-40s\n" "VARIABLE" "VALUE"
printf "%-28s | %-40s\n" "----------------------------" "----------------------------------------"
printf "%-28s | %-40s\n" "PROJECT_NAME" "${PROJECT_NAME:-helixnet}"
printf "%-28s | %-40s\n" "HX_PROJECT_APP_VERSION" "${HX_PROJECT_APP_VERSION:-0.0.1}"
printf "%-28s | %-40s\n" "HX_API_URL" "${HX_API_URL:-http://localhost:8000}"
printf "%-28s | %-40s\n" "ENVIRONMENT" "${ENVIRONMENT:-dev}"
printf "%-28s | %-40s\n" "Postgres" "${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}"
printf "%-28s | %-40s\n" "RabbitMQ" "rabbitmq"
printf "%-28s | %-40s\n" "Redis" "redis"
printf "%-28s | %-40s\n" "Keycloak" "keycloak"
printf "%-28s | %-40s\n" "SECRET_KEY" "$( [[ -z "${SECRET_KEY:-}" ]] && echo "NOT SET" || echo "SET (Len: ${#SECRET_KEY})" )"
echo ""

# ==========================================================
# 🌐 INTERNAL CONNECTIVITY
# ==========================================================
echo -e "\n${BLUE}--- 🌐 INTERNAL NETWORK CHECKS ---${NC}"
for service in postgres redis rabbitmq 🪣️  minio keycloak; do
  check_ping "$service" "$service"
done

# ==========================================================
# ⚡ TRAEFIK HEALTH
# ==========================================================
echo -e "\n${BLUE}--- ⚡ TRAEFIK HEALTH ---${NC}"
if [[ -n "$TRAEFIK_HOST" ]]; then
  echo -e "$INFO Checking Traefik container → ${TRAEFIK_HOST} (${TRAEFIK_DOMAIN})"
  check_http "Traefik /ping" "https://${TRAEFIK_DOMAIN}/ping" 200
  check_http "Traefik Dashboard" "https://${TRAEFIK_DOMAIN}/dashboard/" 200
else
  echo -e "$SKIP Traefik not detected${NC}"
fi

# ==========================================================
# 🔗 EXTERNAL REACHABILITY
# ==========================================================
echo -e "\n${BLUE}--- 🔗 TRAEFIK / LOCALHOST REACHABILITY ---${NC}"
check_http "Web App (Traefik)" "https://${TRAEFIK_DOMAIN}/health" 200
check_http "RabbitMQ UI (Traefik)" "https://rabbitmq.{TRAEFIK_DOMAIN}/" 302
check_http "Web App (Localhost)" "http://localhost:8000/health" 200
check_http "RabbitMQ UI (Localhost)" "http://localhost:15672" 200
check_http "MinIO API (Localhost)" "http://localhost:9090/minio/health/live" 200

# ==========================================================
# 🐳 DOCKER STACK STATUS
# ==========================================================
echo -e "\n${BLUE}--- 🐳 DOCKER STACK STATUS ---${NC}"
COMPOSE_FILE=$(find compose -type f -name "*.yml" | head -n 1 2>/dev/null || true)

if ! command -v docker &>/dev/null; then
  echo -e "$SKIP Docker CLI unavailable${NC}"
elif [[ -z "$COMPOSE_FILE" ]]; then
  echo -e "$SKIP No compose files found${NC}"
elif ! docker info >/dev/null 2>&1; then
  echo -e "$SKIP Docker daemon not running${NC}"
else
  # only print ps output if project is valid
  if docker compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"
  else
    echo -e "$SKIP Stack definition invalid or containers are all down${NC}"
  fi
fi

# ==========================================================
# 🧩 DETERMINE OVERALL STATUS
# ==========================================================
if grep -q "FAIL" <<< "$(history -p "$FAIL")" >/dev/null 2>&1; then
  OVERALL="degraded"
else
  OVERALL="healthy"
fi

if grep -q "FAIL" <<< "$(set +o history; typeset -f)" || grep -q "❌" <<< "$(set +o history; typeset -f)"; then
  OVERALL="degraded"
fi

# ==========================================================
# ✅ SUMMARY
# ==========================================================
echo -e "\n${BLUE}------------------------------------------------${NC}"
echo -e "🥋 ${GREEN}CHUCK NORRIS QA COMPLETE${NC} — Review Results Above"
echo -e "${BLUE}------------------------------------------------${NC}"
echo -e "🌐 Web API: ${BLUE}https://helix-platform.local/docs${NC}"
echo -e "📦 RabbitMQ: ${BLUE}https://rabbitmq-helix.local${NC}"
echo -e "🪣️ MinIO: ${BLUE}http://localhost:9091${NC}"
echo -e "🧠 Keycloak: ${BLUE}https://keycloak.helix.local${NC}"
echo -e "📊 Adminer: ${BLUE}https://adminer.helix.local${NC}"
echo -e "🏁 Host: $(hostname) | In Docker: $IN_DOCKER | Time: $(date +%T)"
echo -e "${BLUE}------------------------------------------------${NC}\n"
echo -e "💥 ${GREEN}If it glows green, it's clean.${NC}"
# ==========================================================
# ✅ SUMMARY & EXIT CODE
# ==========================================================
ELAPSED=$SECONDS
if (( FAIL_COUNT > 0 )); then
  echo -e "\n${RED}🚨 System health degraded ($FAIL_COUNT failed checks).${NC}"
  EXIT_CODE=1
else
  echo -e "\n${GREEN}💚️ All systems healthy.${NC}"
  EXIT_CODE=0
fi

echo -e "⏱️  Duration: ${ELAPSED}s"
echo -e "📦 Build: ${SHA} | Image: ${LATEST_HELIX_IMAGE} | Time: ${BUILD_TIME}\n"
exit $EXIT_CODE

