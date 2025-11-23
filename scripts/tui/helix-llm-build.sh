#!/usr/bin/env bash
# scripts/helix-boot-llm.sh  -- bring up helix-llm (ollama / qdrant / openwebui)
set -euo pipefail
IFS=$'\n\t'

# shellcheck source=/dev/null
source "$(dirname "$0")/tools/helix-utils.sh"
banner_show

echo "🔊 Stage 1: helix-llm (local LLM infra)"
COMPOSE_FILE=$(find_compose_file "helix-llm" || true)

# fallback to existing compose paths if your repo uses old names
if [[ -z "$COMPOSE_FILE" ]]; then
  # check for compose/ollama-service or compose/llm-stack.yml
  if [[ -f "compose/ollama-service/llm-stack.yml" ]]; then
    COMPOSE_FILE="compose/ollama-service/llm-stack.yml"
  elif [[ -f "compose/llm-stack.yml" ]]; then
    COMPOSE_FILE="compose/llm-stack.yml"
  fi
fi

if [[ -z "$COMPOSE_FILE" ]]; then
  echo "⚠️  No helix-llm compose file found, skipping LLM stage"
  exit 0
fi

echo "🗂️  Using compose file: $COMPOSE_FILE"
# gum_spin_safe 2 "Starting helix-llm services..."

docker compose -f "$COMPOSE_FILE" pull --ignore-pull-failures || true
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

# Wait for ollama container if present
if docker compose -f "$COMPOSE_FILE" ps --format '{{.Service}} {{.State}}' | grep -q ollama; then
  # wait for health or port
  # gum_spin_safe 4 "Waiting for Ollama to come online..."
  # If container exists, we can check port 11434
  if curl -sf --max-time 3 http://localhost:11434/ >/dev/null 2>&1; then
    echo "✅ Ollama listening on 11434"
  else
    echo "⚠️  Ollama may need more time. Check logs: docker compose -f $COMPOSE_FILE logs -f ollama"
  fi
fi

echo "✅ helix-llm stage complete"
