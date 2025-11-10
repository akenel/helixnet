#!/usr/bin/env bash
set -Eeuo pipefail
# --- Directories ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$PROJECT_ROOT/compose"
# --- Docker Compose ---
COMPOSE="docker compose"
echo "🚀 Starting stack.sh ..."
echo "📂 Current working directory: $(pwd)"
echo "📦 Compose directory: $COMPOSE_DIR"
case "${1:-}" in
  up)
    echo "🚀 Composing stacks:"
    echo "🌍 EDGE 🏹️ | 🔐 AUTH 🏹️ | 🍏 CORE 🏹️ | 🧠 HELIX 🐰️"
    # Stop and remove existing containers to avoid conflicts
    docker stop rabbitmq  && docker rm rabbitmq
    docker stop minio     && docker rm minio
    docker stop redis     && docker rm redis
    docker stop worker    && docker rm worker
    docker stop postgres  && docker rm postgres
    docker stop flower    && docker rm flower
    cd "$COMPOSE_DIR"
    $COMPOSE \
      -f edge-stack.yml \
      -f auth-stack.yml \
      -f core-stack.yml \
      -f helix-stack.yml \
      --profile edge \
      --profile auth \
      --profile core \
      --profile helix \
      up -d
    ;;
  down)
    echo "⛔ Shutting down all containers..."
    cd "$COMPOSE_DIR"
    $COMPOSE down
    ;;
  core)
    echo "🍏 Starting core stack..."
    cd "$COMPOSE_DIR"
    $COMPOSE --profile core -f core-stack.yml up -d
    ;;
  helix)
    echo "🧠 Starting Helix stack..."
    cd "$COMPOSE_DIR"
    $COMPOSE --profile helix -f helix-stack.yml up -d
    ;;
edge)
	echo "🌍 Stopping and removing EDGE stack..."
	- docker stop traefik 2>/dev/null || true
	- docker stop portainer 2>/dev/null || true
	- docker rm traefik 2>/dev/null || true
	- docker rm portainer 2>/dev/null || true
	cd $COMPOSE_DIR
	$COMPOSE --profile edge -f edge-stack.yml build --no-cache
	$COMPOSE --profile edge -f edge-stack.yml up -d
	echo "🌍 Started edge stack..."
	;;
  auth)
    echo "🔐 Stopping and removing AUTH Stack..."
    # docker down --remove-orphans
    docker stop keycloak   && docker rm keycloak 
    docker stop postgres   && docker rm postgres
    docker stop pgadmin    && docker rm pgadmin  
    docker stop vault      && docker rm vault
    make edge
    cd "$COMPOSE_DIR"
    $COMPOSE --profile auth -f auth-stack.yml up -d
    echo "🔐  Started auth stack..."
    ;;
  rebuild)
    echo "♻️ Rebuilding stack..."
    cd "$COMPOSE_DIR"
    $COMPOSE down --remove-orphans
    $COMPOSE build --no-cache
    $COMPOSE up -d
    ;;
  clean)
    echo "🧹 Removing all images and volumes..."
    docker system prune -af --volumes
    ;;
  doctor)
    echo "🧠 Running diagnostics..."
    docker ps -a
    docker images | grep helix || echo "⚠️ Missing Helix images."
    ;;
  *)
    echo "Usage: stack.sh {up|down|core|auth|helix|edge|rebuild|clean|doctor}"
    exit 1
    ;;
esac
