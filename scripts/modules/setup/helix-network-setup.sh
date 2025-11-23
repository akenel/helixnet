#!/usr/bin/env bash
# =================================================================
# 🌐 HelixNet Infrastructure Setup
# Idempotently creates Docker networks and builds base images.
# =================================================================
set -euo pipefail
IFS=$'\n\t'
# --- Colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;36m'; NC='\033[0m'
OK="${GREEN}✅${NC}"; WARN="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
BUILD="${YELLOW}🏗️${NC}"
# -----------------------------------------------------------------
# Idempotent Network Creator
# Creates a Docker network only if it doesn't already exist.
# Args: $1 = network name
# -----------------------------------------------------------------
create_network_if_not_exists() {
    local network_name="$1"
    
    # Check if the network already exists
    if docker network inspect "$network_name" &>/dev/null; then
        echo -e "${OK} Network '$network_name' already exists. Skipping creation. ${NC}"
        return 0
    fi
    
    echo -e "${INFO} Creating network '$network_name'...${NC}"
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
# Idempotent Volume Builder
# -----------------------------------------------------------------
create_volume_if_not_exists() {
    local v="$1"
    if docker volume inspect "$v" &>/dev/null; then
        echo -e "${OK} Volume '$v' exists."
    else
        echo -e "${INFO} Creating volume '$v'..."
        docker volume create "$v"
    fi
}

# -----------------------------------------------------------------
# Idempotent Image Builder
# Builds a Docker image only if the target tag does not exist locally.
# Args: 
#   $1 = image tag (e.g., helix-base)
#   $2 = Dockerfile path (e.g., compose/helix-main/Dockerfile.base)
#   $3 = Build context path (e.g., .)
# -----------------------------------------------------------------
build_image_if_not_exists() {
    local image_tag="$1"
    local dockerfile_path="$2"
    local context_path="$3"

    # Check if the image tag exists locally
    if [[ -n "$(docker images -q "$image_tag" 2>/dev/null)" ]]; then
        echo -e "${OK} Image '$image_tag' found locally. Skipping build. ${NC}"
        return 0
    fi

    echo -e "${BUILD} Image '$image_tag' not found. Starting build from ${dockerfile_path}...${NC}"
    
    # Run the docker build command
    # Assuming this script is executed from the project root for the context_path ('.') to work.
    docker build -t "$image_tag" -f "$dockerfile_path" "$context_path"
    
    if [[ $? -eq 0 ]]; then
        echo -e "${OK} Image '$image_tag' built successfully.${NC}"
    else
        echo -e "${FAIL} Failed to build image '$image_tag'. Check Dockerfile errors.${NC}"
        return 1
    fi
}

# -----------------------------------------------------------------
# Idempotent Volume Creator
# Creates a Docker volume only if it doesn't already exist.
# -----------------------------------------------------------------
create_volume_if_not_exists() {
    local volume_name="$1"

    # Already exists?
    if docker volume inspect "$volume_name" &>/dev/null; then
        echo -e "${OK} Volume '$volume_name' already exists. Skipping. ${NC}"
        return 0
    fi

    echo -e "${INFO} Creating volume '$volume_name'...${NC}"
    docker volume create "$volume_name" &>/dev/null

    if [[ $? -eq 0 ]]; then
        echo -e "${OK} Volume '$volume_name' created successfully.${NC}"
    else
        echo -e "${WARN} Failed to create volume '$volume_name'.${NC}"
        return 1
    fi
}
