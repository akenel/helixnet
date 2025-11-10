#!/usr/bin/env bash
# ==========================================================
# 🥋 HelixNet Health Matrix – "Forged Bronze Edition"
# ==========================================================
# Author: Angel 🧩 Refactored by Sherlock
# Purpose: Unified system health check for the HelixNet stack
# ----------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

# ==========================================================
# 🧱 BUILD INFO
# ==========================================================
LATEST_HELIX_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "helix-web_" | head -n 1 || true)
BUILD_TIME=$(echo "$LATEST_HELIX_IMAGE" | sed 's/.*helix-web_//;s/_.*//' || echo "N/A")
BUILD_SHA=$(echo "$LATEST_HELIX_IMAGE" | sed 's/.*_//' || echo "local")

echo ""
echo "--------------------------------------------------"
echo "🏗️  HELIX BUILD INFO"
echo "--------------------------------------------------"
printf "Image:      %s\n" "${LATEST_HELIX_IMAGE:-N/A}"
printf "Timestamp:  %s\n" "${BUILD_TIME:-N/A}"
printf "Git SHA:    %s\n" "${BUILD_SHA:-local}"
echo ""

# ==========================================================
# 🎨 COLOR CODES
# ==========================================================
GREEN='\033[32m'; RED='\033[31m'; YELLOW='\033[33m'; BLUE='\033[36m'; NC='\033[0m'
OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; SKIP="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"

# ==========================================================
# 📦 ENVIRONMENT LOADING
# ==========================================================
ENV_FILE=".env"
[ ! -f "$ENV_FILE" ] && [ -f "../.env" ] && ENV_FILE="../.env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  set -a; source "$ENV_FILE"; set +a
  echo -e "${INFO} Configuration loaded from → ${ENV_FILE}${NC}"
else
  echo -e "${FAIL} ERROR:${NC} No .env file found!"
fi

# ==========================================================
# 🧠 ENVIRONMENT CONTEXT
# ==========================================================
IN_DOCKER=false
[[ -f /.dockerenv ]] && IN_DOCKER=true

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
  fi
}

# ==========================================================
# 🧩 HELPER: INTERNAL PING (Docker network)
# ==========================================================
check_ping() {
  local NAME="$1"; local HOST="$2"
  if command -v docker &>/dev/null; then
    if docker compose ps 2>/dev/null | grep -q "$NAME.*running"; then
      docker run --rm --network "${PROJECT_NAME:-helix}_public" busybox ping -c1 -W1 "$HOST" >/dev/null 2>&1 \
        && echo -e "$OK ${GREEN}OK${NC} $NAME ($HOST)" \
        || echo -e "$FAIL ${RED}FAIL${NC} $NAME ($HOST)"
    else
      echo -e "$SKIP ${YELLOW}SKIP${NC} $NAME ($HOST) - container not running"
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
printf "%-28s | %-40s\n" "SECRET_KEY" "$( [[ -z "${SECRET_KEY:-}" ]] && echo "${RED}NOT SET${NC}" || echo "${GREEN}SET (Len: ${#SECRET_KEY})${NC}" )"
echo ""

# ==========================================================
# 🌐 INTERNAL CONNECTIVITY
# ==========================================================
echo -e "\n${BLUE}--- 🌐 INTERNAL NETWORK CHECKS ---${NC}"
for service in postgres redis rabbitmq minio keycloak; do
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
check_http "RabbitMQ UI (Traefik)" "https://${TRAEFIK_DOMAIN}/rabbitmq" 302
check_http "MinIO Console (Traefik)" "https://${TRAEFIK_DOMAIN}/minio/login" 302
check_http "Web App (Localhost)" "http://localhost:8000/health" 200
check_http "RabbitMQ UI (Localhost)" "http://localhost:15672" 200
check_http "MinIO API (Localhost)" "http://localhost:9090/minio/health/live" 200

# ==========================================================
# 🐳 DOCKER STACK STATUS
# ==========================================================
echo -e "\n${BLUE}--- 🐳 DOCKER STACK STATUS ---${NC}"
COMPOSE_FILE=$(find compose -type f -name "*.yml" | head -n 1 2>/dev/null || true)
if command -v docker &>/dev/null && [[ -n "$COMPOSE_FILE" ]]; then
  docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"
else
  echo -e "$SKIP No docker-compose.yml found or Docker unavailable${NC}"
fi

# ==========================================================
# ✅ SUMMARY
# ==========================================================
echo -e "\n${BLUE}------------------------------------------------${NC}"
echo -e "🥋 ${GREEN}CHUCK NORRIS QA COMPLETE${NC} — Review Results Above"
echo -e "${BLUE}------------------------------------------------${NC}"
echo -e "🌐 Web API: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "📦 RabbitMQ: ${BLUE}http://localhost:15672${NC}"
echo -e "🗄️ MinIO: ${BLUE}http://localhost:9091${NC}"
echo -e "🧠 Keycloak: ${BLUE}http://localhost:8080/admin${NC}"
echo -e "📊 PGAdmin: ${BLUE}http://localhost:5050${NC}"
echo -e "🏁 Host: $(hostname) | In Docker: $IN_DOCKER | Time: $(date +%T)"
echo -e "${BLUE}------------------------------------------------${NC}\n"
echo -e "💥 ${GREEN}If it glows green, it's clean.${NC}"
