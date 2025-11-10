#!/usr/bin/env bash
# ==========================================================
# 💥 ERROR TRAP: Catches an error and prints the line number
# ==========================================================
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
set -euo pipefail
# Set colors for output
CHECK="🚬️"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
CYAN='\033[0;39m'
NC='\033[0m' # No Color
# --- Clipboard Helper ---
# This function checks for multiple clipboard utilities in order of preference:
# 1. pbcopy (macOS)
# 2. xclip (Linux/X11)
# 3. xsel (Linux/X11)
# 4. clip.exe (Windows/WSL)
copy_to_clipboard() {
  local text="$1"

  if command -v pbcopy &>/dev/null; then
    echo -n "$text" | pbcopy
    echo -e "${GREEN}📋 Copied to clipboard (macOS)${NC}"
  elif command -v xclip &>/dev/null; then
    echo -n "$text" | xclip -selection clipboard
    echo -e "${GREEN}📋 Copied to clipboard (xclip)${NC}"
  elif command -v xsel &>/dev/null; then
    echo -n "$text" | xsel --clipboard --input
    echo -e "${GREEN}📋 Copied to clipboard (xsel)${NC}"
  elif command -v clip.exe &>/dev/null; then
    # New logic for Windows Subsystem for Linux (WSL)
    echo -n "$text" | clip.exe
    echo -e "${GREEN}📋 Copied to clipboard (Windows/WSL)${NC}"
  else
    echo -e "${YELLOW}⚠️  Clipboard not available. Please install xclip or xsel.${NC}"
  fi
}
echo "🧩 Exporting environment variables from .env..."
echo "---------------------------------------------------------"
echo "System env are docker set now 🧩 cleanse via ./scripts/helix-nuke.sh ✅"
docker system df
set -a
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "$line" ]] && continue
  if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
    key="${line%%=*}"
    val="${line#*=}"
    export "$key"="${val}"
  fi
done < .env

set +a

# Confirm a few critical envs
echo "✅ Key vars loaded:"
echo "   - HX_ENVIRONMENT=$HELIX_ENVIRONMENT"
echo "   - POSTGRES_USER=$POSTGRES_USER"
echo "   - KEYCLOAK_ADMIN_USER=$KEYCLOAK_ADMIN_USER"
echo "   - RABBITMQ_USER=$RABBITMQ_USER"
echo "   - REDIS_DB=$REDIS_DB"
# port diagnostics
echo "🔍 Checking for common port conflicts..."

# FIX START: Wrap in subshell to disable pipefail for the port check loop
(
    # Temporarily disable pipefail. The grep command below exits with 1 when no LISTEN 
    # matches are found, which is expected behavior but crashes the script under pipefail.
    set +o pipefail
    for port in 8080 8888 80 443; do
      if sudo lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is in use by:"
        # Line 44 fixed by the subshell's `set +o pipefail`
        sudo lsof -i :$port | grep LISTEN | awk '{print "   → PID " $2 " (" $1 ")"}'
      else
        echo "✅ Port $port is free."
      fi
    done
)
# FIX END

echo "---------------------------------------------------------"

# --- IDEMPOTENT NETWORK CREATION FIX ---
echo "⚙️ Checking and creating required Docker networks..."

# Function to safely create a network (only if it doesn't exist)
create_network_if_not_exists() {
    local NETWORK_NAME="$1" # Use local and quotes for safety
    # We inspect the network. If it fails (exit code 1), the network doesn't exist.
    # We suppress the "not found" output (2>/dev/null) as it is expected when missing.
    if ! docker network inspect "$NETWORK_NAME" &> /dev/null; then
        echo "   -> Creating network: ${NETWORK_NAME}..."
        # Create the network. If this fails, the script should crash (because Docker is truly broken).
        docker network create "$NETWORK_NAME" > /dev/null
    else
        echo "   -> Network ${NETWORK_NAME} already exists. Proceeding."
        # docker network inspect --format '{{json .Config.Subnets}}' ${NETWORK_NAME}
    fi
}

create_network_if_not_exists int_core
create_network_if_not_exists edge_public

# Display network list after check
docker network ls

# --- END IDEMPOTENT NETWORK CREATION FIX ---
echo "--- 💦️ HelixNet BOOTSTRAP 👣️ Bringing up all stacks ------------------------"
# Bring up all stacks
echo "👨‍🍳️ HelixNet BOOTSTRAP: Bringing up all stacks (auth, core, helix, edge)..."
echo " 👣️ Give the base image a local tag and reference it"
echo "  💪️  Build the base image once with a local name:"
export BUILDKIT_PROGRESS=plain
docker build -t helix-base -f compose/celery/Dockerfile.base .
echo "🛠️ FYI: docker compose Command structure: -p <project> -f <files> up -d --build --remove-orphans --wait"
DOCKER_BUILDKIT=1 
docker compose \
  -p helix \
  -f compose/auth-stack.yml \
  -f compose/core-stack.yml \
  -f compose/helix-stack.yml \
  -f compose/edge-stack.yml \
  up -d --build --pull always --force-recreate --remove-orphans --wait
sleep 5
# Optional health checks
echo "🩺 Checking container health. RUN > docker logs postgres and keycloak, helix, worker, etc."
echo "---------------------------------------------------------"
echo "System is now running."

# 4. Final Verification
echo "---------------------------------------------------------"
echo "✅ Docker compose complete. Final System Status:"

echo "Volumes (list):"
docker volume ls

echo "Images (list):"
docker image ls

echo "---------------------------------------------------------"
echo "Storage check:"
docker system df
echo "---------------------------------------------------------"
echo "---------------------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo "---------------------------------------------------------"
echo "✅ HelixNet  system df info 🚥️ 🚢️ .env + docker + settings 👀️ "
docker system df
# echo "---------------------------------------------------------"
# docker ps --format "table {{.Names}}\t{{.Status}}"
# echo "✅  docker ps --format ^ table {{.Names}}\t{{.Status}} ^ "

ls -lt scripts
echo "⛑️ Example :         ./scripts/helix-status.sh        ---"
# echo ""
# echo "---------------------------------------------------------"
# echo "---------------------------------------------------------"
# echo "💦️ 🐘️ docker logs helix --tail=20 🦄  Main FastAPI Core"
# echo "---------------------------------------------------------"
# docker logs helix --tail=20
# echo "---------------------------------------------------------"
# echo "---------------------------------------------------------"
# echo ""
# Check if docker is available
if ! command -v docker &> /dev/null
then
    echo -e "${RED}Error: docker command not found. Ensure Docker is installed and running.${NC}"
    exit 1
fi

LOG_TAIL=10

echo -e "${CYAN}---- Double checking docker logs again -------${NC}"
echo -e "${YELLOW}🚨 Diagnosing Worker (Celery) Connection Refused (RabbitMQ Dependency) ${NC}"
echo -e "${CYAN}---------------------------------------------------------${NC}"
sleep 3
# 1. RabbitMQ Logs: Find out why it's refusing the connection from the worker
echo -e "${GREEN}🐰 rabbitmq Logs (Last $LOG_TAIL lines)${NC}"
docker logs rabbitmq --tail=$LOG_TAIL

echo -e "${CYAN}---------------------------------------------------------${NC}"

# 2. Worker Logs: Confirming the repeated connection failure
echo -e "${GREEN}🥬 worker Logs (Last $LOG_TAIL lines) - Look for connection string issues ${NC}"
docker logs worker --tail=$LOG_TAIL

echo -e "${CYAN}---------------------------------------------------------${NC}"
echo -e "${YELLOW}🚨 Diagnosing Helix (The Orchestrator) Startup Block (Keycloak Dependency) ${NC}"
echo -e "${CYAN}---------------------------------------------------------${NC}"

# 3. Keycloak Logs: Helix is waiting for this (and Postgres, which is healthy)
echo -e "${GREEN}👑 keycloak Logs (Last $LOG_TAIL lines) - Check for successful startup or errors ${NC}"
docker logs keycloak --tail=$LOG_TAIL

echo -e "${CYAN}---------------------------------------------------------${NC}"

# 4. Helix Logs: See what it is currently attempting
echo -e "${GREEN}💡 helix Logs (Last $LOG_TAIL lines) - Should show Keycloak readiness status ${NC}"
docker logs helix --tail=$LOG_TAIL

echo -e "${CYAN}---------------------------------------------------------${NC}"
echo -e "${GREEN}✅ Diagnostic complete. Review the RabbitMQ and Keycloak logs above.${NC}"
echo "---------------------------------------------------------"
echo "🧩️ docker logs beat --tail=20 🧩️ beat: Task Scheduler Clock"
echo "---------------------------------------------------------"
docker logs beat --tail=20
echo "---------------------------------------------------------"
echo "---------------------------------------------------------"
echo "🥬️ docker logs worker --tail=20 🥬️ worker: Celery Job Runner"
echo "---------------------------------------------------------"
docker logs worker --tail=20
echo "---------------------------------------------------------"
echo "---------------------------------------------------------"
echo "🌼 docker logs flower --tail=20 🌼 flower: Celery Monitor"
echo "---------------------------------------------------------"
docker logs flower --tail=20
echo "---------------------------------------------------------"
echo "---------------------------------------------------------"
echo "🦄 docker logs helix --tail=20 FastAPI Core Service"
echo "---------------------------------------------------------"
docker logs helix --tail=20
echo "---------------------------------------------------------"

# | Context                  | Example                          | Purpose                                                        |
# | ------------------------ | -------------------------------- | -------------------------------------------------------------- |
# | **OS user**              | `root`, `postgres`, `helix_user` | Linux-level account running the PostgreSQL service             |
# | **Database user (role)** | `postgres`, `helix_user`         | PostgreSQL-level account that can connect to and own databases |
docker exec -it postgres psql -U postgres
\du
\l
# --- Optional clipboard injection ---
copy_to_clipboard "./scripts/helix-boot.sh"

echo -e "${BLUE}You can now paste and run:${NC} ./scripts/helix-boot.sh 🚀"
echo -e "\n${CHECK} ${GREEN}Docker environment reset 💦️ complete!${NC}"

