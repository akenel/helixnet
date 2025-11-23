#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

CORE="${ROOT_DIR}/compose/helix-core/core-stack.yml"
MAIN="${ROOT_DIR}/compose/helix-main/main-stack.yml"
LLM="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"

echo "🛑 Stopping Helix stacks..."

stop_stack() {
  local FILE="$1"

  if [[ -f "$FILE" ]]; then
    echo "➡️  Stopping stack: $FILE"
    docker compose -f "$FILE" down --remove-orphans 2>/dev/null || true
  else
    echo "⚠️  Missing stack file: $FILE"
  fi
}

stop_stack "$LLM"
stop_stack "$MAIN"
stop_stack "$CORE"

echo "🔍 Removing stray containers..."
docker ps -a --format '{{.Names}}' | grep -E '^helix' || true | xargs -r docker rm -f

echo "📦 Cleaning Helix networks ONLY..."
docker network ls --format '{{.Name}}' | grep '^helixnet' | xargs -r docker network rm || true

echo "🧹 Basic prune (no volumes removed)..."
docker system prune -f >/dev/null

echo "✅ Helix shutdown complete."
