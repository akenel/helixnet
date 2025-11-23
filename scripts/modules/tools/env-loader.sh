#!/usr/bin/env bash
# =================================================================
# 🌐 HelixNet Network Setup
# Idempotently creates Docker networks required by the Helix stack.
# =================================================================
set -euo pipefail
IFS=$'\n\t'

# --- Colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;36m'; NC='\033[0m'
OK="${GREEN}✅${NC}"; WARN="${YELLOW}⚠️${NC}"

# -----------------------------------------------------------------
# Idempotent Network Creator
# Creates a Docker network only if it doesn't already exist.
# Args: $1 = network name
# -----------------------------------------------------------------
create_network_if_not_exists() {
    local network_name="$1"
    # Check if the network argument exists
    if network_name=""; then
    echo -e "${OK} Network name '$network_name' empty. Skipping creation. ${NC}"
    return 0
    echo -e "${BLUE}ℹ️ Initiate Network '$network_name' request...${NC}"
    fi  
    # Check if the network already exists
    if docker network inspect "$network_name" &>/dev/null; then
        echo -e "${OK} Network '$network_name' already exists. Skipping creation. ${NC}"
        return 0
    fi
    
    echo -e "${BLUE}ℹ️   Creating network '$network_name'...${NC}"
    # Use the --attachable flag for flexibility (optional, but good practice)
    if docker network create "$network_name" &>/dev/null; then
        echo -e "${OK} Network '$network_name' created successfully.${NC}"
    else
        # This fallback usually won't be hit due to the inspect check, 
        # but handles rare cases where creation fails for other reasons.
        echo -e "${WARN} Failed to create network '$network_name'. It might still exist or be in use.${NC}"
        return 1
    fi
}

# -----------------------------------------------------------------
# Execution Block
# -----------------------------------------------------------------
echo -e "${BLUE}Creating the Helix Networks now: helixnet_core and helixnet_edge...${NC}"

create_network_if_not_exists "helixnet_core"
create_network_if_not_exists "helixnet_edge"

echo -e "${GREEN}Network setup complete.${NC}"
# show_main_menu # <-- Placeholder for your main application logic

# The script can now exit cleanly or continue to your main menu logic
# return 0