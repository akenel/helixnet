#!/bin/bash
# =============================================================================
# VIDEO 3: Self-Healing Demo Script
# =============================================================================
# Just run this and watch. Narrate during or after.
# Total runtime: ~45 seconds
# =============================================================================

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

clear

echo -e "${CYAN}${BOLD}"
echo "=============================================="
echo "  HELIXNET SELF-HEALING DEMO"
echo "=============================================="
echo -e "${NC}"
sleep 3

# Step 1: Show current healthy state
echo -e "${GREEN}${BOLD}>>> STEP 1: Current Status - Redis is Healthy${NC}"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAMES|redis|autoheal"
echo ""
sleep 5

# Step 2: Crash redis
echo -e "${RED}${BOLD}>>> STEP 2: Crashing Redis (kill PID 1 inside container)${NC}"
echo ""
echo -e "${YELLOW}$ docker exec redis kill 1${NC}"
docker exec redis kill 1 2>/dev/null
echo ""
echo -e "${RED}Redis process killed. Container will restart automatically...${NC}"
echo ""
sleep 3

# Step 3: Show it restarting
echo -e "${YELLOW}${BOLD}>>> STEP 3: Redis Restarting (5 seconds later)${NC}"
echo ""
sleep 5
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAMES|redis"
echo ""
sleep 3

# Step 4: Show it back to healthy
echo -e "${GREEN}${BOLD}>>> STEP 4: Waiting for Health Check (15 seconds)${NC}"
echo ""
for i in {15..1}; do
    printf "\r  Checking in %2d seconds... " "$i"
    sleep 1
done
echo ""
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAMES|redis"
echo ""
sleep 2

# Final message
echo -e "${GREEN}${BOLD}"
echo "=============================================="
echo "  SELF-HEALING COMPLETE"
echo "  Redis crashed and recovered automatically."
echo "  No human intervention. No pager. No 3am call."
echo "=============================================="
echo -e "${NC}"
sleep 5

echo -e "${CYAN}Demo complete. Press any key to exit.${NC}"
read -n 1 -s
