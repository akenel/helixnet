#!/usr/bin/env bash
# ==========================================================
# 💥 ERROR TRAP: Catches an error and prints the line number
# ==========================================================
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
set -euo pipefail

echo "💥 HelixNet NUKE SCRIPT: Stopping, removing containers, networks, and volumes..."
echo "🚨 This command DESTROYS all current data in Postgres, Redis, MinIO, Keycloak, and Portainer volumes!"
# IMPORTANT: Docker Compose needs the files loaded before DOWN can correctly identify resources.
docker compose \
    -p helix \
    -f compose/auth-stack.yml \
    -f compose/core-stack.yml \
    -f compose/helix-stack.yml \
    -f compose/edge-stack.yml \
    down -v
echo "✅ HelixNet stack successfully destroyed volumes. Now, './scripts/helix-boot.sh'"
echo "✅ 👀️ 🔐️ 🥬️ 🐰️ 💦️  🐘️ ⛏️  🐖️ 🌐️ 🍏️ ⛑️  🌸️ ❤️  🪵️  ⛽️ 🚧️ 🚥️ 🚢️ 💧️ 🔥️ 🐫️ ❄️  ⚡️ 🕹️"
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
echo "Active Networks (list):"
docker network ls
echo "---------------------------------------------------------"
echo "✅ HelixNet Docked Down 🚥️ 🚢️ .env + docker + settings 👀️ "
docker system df
echo "---------------------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo "✅  docker ps --format ^ table {{.Names}}\t{{.Status}} ^ "
ls -lt scripts

