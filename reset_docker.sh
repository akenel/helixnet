#!/usr/bin/env bash
set -euo pipefail

echo "🔥 Sherlock's Docker Reset: stopping and removing EVERYTHING..."

# Stop all containers
docker ps -aq | xargs -r docker stop

# Remove all containers
docker ps -aq | xargs -r docker rm -f

# Remove all networks except default (bridge, host, none)
for net in $(docker network ls --quiet); do
  name=$(docker network inspect --format '{{.Name}}' "$net")
  if [[ "$name" != "bridge" && "$name" != "host" && "$name" != "none" ]]; then
    docker network rm "$net" || true
  fi
done

# Remove all dangling/unused volumes
docker volume ls -q | xargs -r docker volume rm || true

# Remove all dangling/unused images
docker image prune -af

# System prune
docker system prune -af --volumes

echo "✅ All containers, volumes, and networks wiped clean."
echo "🚀 You can now run ./setup.sh again and deploy fresh."
