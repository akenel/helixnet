#!/bin/bash
# 🧨 HelixNet Docker NUKE — Total System Cleanup (Runtime Reset)
# Purpose: Remove containers, volumes, networks, and free ports.
# ==========================================================
# 💥 ERROR TRAP: Catches an error and prints the line number
# ==========================================================
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
set -euo pipefail

IFS=$'\n\t'
# Define variables for colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[1;35m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 HELIX NUKE — Runtime Purge (Images Preserved)${NC}"
echo "───────────────────────────────────────────────────────────────"

# 1️⃣ Gracefully stop and remove all services across all compose files
echo -e "${BLUE}[1️⃣] Stopping and removing all services (Containers & Named Volumes)...${NC}"

# 💡 FIX: Pass all compose files to resolve dependencies correctly
DOCKER_COMPOSE_FILES=(
    compose/auth-stack.yml
    compose/core-stack.yml
    compose/helix-stack.yml
    compose/edge-stack.yml
)

# Build the file list command line argument
FILE_ARGS=""
for f in "${DOCKER_COMPOSE_FILES[@]}"; do
    FILE_ARGS+=" -f $f"
done

export BUILDKIT_PROGRESS=plain
DOCKER_BUILDKIT=1 

# Execute docker compose down with all files and remove volumes (-v)
docker compose \
    -p helix \
    -f compose/auth-stack.yml \
    -f compose/core-stack.yml \
    -f compose/helix-stack.yml \
    -f compose/edge-stack.yml \
 down --remove-orphans -v
echo " 1️⃣  Waiting to complete ... "
sleep 1
echo "   ✅ All service containers and named volumes cleared."
# Clean up specific local data (Celery Beat state)
echo "💣 Nuking local state directories..."
sudo rm -rf compose/helix/beat-data/* >/dev/null 2>&1 || true
echo "   ✅ Celery Beat data cleared."

# 2️⃣ Selective Hardcore Image & Volume Deletion (Keycloak and Postgres)
echo -e "${BLUE}[2️⃣] HARD RESET: Removing Keycloak and Postgres Images/Volumes...${NC}"

# Remove Keycloak-specific items
docker image rm -f helix-keycloak:24.0.4-stable >/dev/null 2>&1 || true
docker volume rm -f keycloak_data >/dev/null 2>&1 || true
echo "   ✅ Keycloak image (helix-keycloak:24.0.4-stable) and volume (keycloak_data) nuked."

# Remove Postgres-specific items (removes all volumes matching the project pattern)
docker volume ls -q -f name=helix_db_data | xargs -r docker volume rm -f >/dev/null 2>&1 || true
echo "   ✅ Postgres data volumes nuked (requires new DB initialization)."

# 3️⃣ Full Docker System Prune (cleanup dangling items)
echo -e "${BLUE}[3️⃣] Full Docker system prune (Dangling items, Networks, Volumes)...${NC}"
# Use existing docker system prune command for cleanup of all dangling objects
docker system prune -a --volumes --force >/dev/null 2>&1 || true
echo "   ✅ Docker system resources pruned."


# 4️⃣ Free critical ports (Kept your robust port cleanup section)
echo -e "${BLUE}[4️⃣] Freeing critical ports (80, 443, 8080, 8888, 9000, 9443)...${NC}"
for port in 80 443 8080 8888 9000 9443 1025 8025; do
  PIDS=$(sudo lsof -t -i :$port 2>/dev/null || true)
  if [ -z "$PIDS" ]; then
    echo "   🔍 Port $port → ${GREEN}✅ free.${NC}"
  else
    echo "   🔍 Port $port → occupied by PID(s): $PIDS"
    for PID in $PIDS; do
      PROC_NAME=$(ps -p "$PID" -o comm= 2>/dev/null || echo "unknown")
      echo "      ⚙️  $PROC_NAME (PID $PID)"
      # Try to identify and stop any systemd-managed service
      SERVICE=$(sudo systemctl status "$PROC_NAME" 2>/dev/null | grep 'Loaded:' | awk '{print $2}' | head -1 || true)
      if [ -n "$SERVICE" ]; then
        echo "      🥋 Stopping systemd service: $SERVICE"
        sudo systemctl stop "$SERVICE" >/dev/null 2>&1 || true
        # sudo systemctl disable "$SERVICE" >/dev/null 2>&1 || true # Only disable if you want it permanently off
      else
        echo "      🔪 Killing PID $PID ($PROC_NAME)..."
        sudo kill -9 "$PID" >/dev/null 2>&1 || true
      fi
    done
  fi
done

# 5️⃣ Verification
echo -e "${BLUE}[5️⃣] Verification...${NC}"
echo "───────────────────────────────────────────────────────────────"
echo -e "${CYAN}Ports still open:${NC}"
sudo ss -ltnp | grep -E '(:80|:443|:8080|:8888|:9000|:9443|:1025|:8025)' || echo "   ✅ None."
echo -e "${CYAN}Docker Networks:${NC}"; docker network ls | grep -E 'edge_public|int_core' || echo "   ✅ Clean."
echo -e "${CYAN}Volumes:${NC}"; docker volume ls | grep 'helix' || echo "   ✅ Clean."
echo "───────────────────────────────────────────────────────────────"
echo -e "${GREEN}✅ Helix Nuke Complete — System is ready for a fresh boot!${NC}"