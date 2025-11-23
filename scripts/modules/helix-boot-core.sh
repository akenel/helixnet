#!/usr/bin/env bash
# scripts/modules/helix-boot-core.sh
# Boots the Core Infrastructure stack (Postgres, Traefik, Keycloak, etc.).

set -euo pipefail
IFS=$'\n\t'

# Source utilities from the scripts/modules/tools directory
source "$(dirname "${BASH_SOURCE[0]}")/tools/helix-utils.sh"

# --- Main Execution ---

banner_show
echo "🔊 Stage 2: core-stack (infra)"

# 1. Find the appropriate compose file
COMPOSE_FILE=$(find_compose_file core-stack)
if [[ -z "$COMPOSE_FILE" ]]; then
    COMPOSE_FILE=$(find compose -maxdepth 2 -type f -iname '*core*.yml' -print -quit 2>/dev/null || true)
fi

if [[ -z "$COMPOSE_FILE" ]]; then
    die "Could not find a docker-compose file for core-stack."
fi
echo "🗂️  Using compose file: $COMPOSE_FILE"

# 2. Network Check/Creation (The KIC KIX Permanent Fix)
# We ensure 'helixnet_edge' and 'helixnet_core' exist here. If they are already present
# from previous runs, the utility function will reuse them.
print_header "🌐 Checking Required Docker Networks"
create_network_if_not_exists "helixnet_edge"
create_network_if_not_exists "helixnet_core"

# 3. Bring up core services
gum_spin_safe 2 'Bringing up core infra...' || true

# Check for required build images (Keycloak is often the only one)
if grep -q 'build:' "$COMPOSE_FILE"; then
    echo "🔨 Local builds detected. Running docker compose build..."
    docker compose -f "$COMPOSE_FILE" build
fi

# Run the compose up command
docker compose -f "$COMPOSE_FILE" up -d

# 4. Wait for critical services to become healthy
print_header "⏱️ Waiting for Critical Core Services"
wait_for_service_healthy postgres 60 || die "Postgres failed to start."
wait_for_service_healthy rabbitmq 60 || die "RabbitMQ failed to start."
wait_for_service_healthy redis 60 || die "Redis failed to start."
wait_for_service_healthy keycloak 120 || die "Keycloak failed to start."
wait_for_service_healthy traefik 60 || die "Traefik failed to start."

echo "✅ core-stack stage complete"