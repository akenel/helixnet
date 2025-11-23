#!/usr/bin/env bash
set -e
# -------------------------------------------------------
# 🌊 Helix Minimal Smart Boot (Restart-Safe)
# No flags, no branching — always works the same way.
# -------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_CORE="${ROOT_DIR}/compose/helix-core/core-stack.yml"
COMPOSE_MAIN="${ROOT_DIR}/compose/helix-main/main-stack.yml"
COMPOSE_LLM="${ROOT_DIR}/compose/helix-llm/llm-stack.yml"
# --- NEW LINE: Define the Environment File Path ---
ENV_FILE="${ROOT_DIR}/env/helix.env"
# --- Simple UI Helpers (text + emojis, no sound) ---
info() { echo "🔹 $1"; }
ok()   { echo "✅ $1"; }
warn() { echo "⚠️  $1"; }
err()  { echo "❌ $1"; exit 1; }
# -------------------------------------------------------
# Ensure Docker networks exist (important for 2nd runs)
# -------------------------------------------------------
ensure_network() {
  local NET="$1"

  if ! docker network ls --format '{{.Name}}' | grep -q "^${NET}$"; then
    info "Creating network: $NET"
    docker network create "$NET" >/dev/null 2>&1 || err "Failed to create network: $NET"
  else
    ok "Network exists: $NET"
  fi
}
ensure_all_networks() {
  info "Checking required networks..."
  local NETWORKS=("helixnet_core" "helixnet_edge")
  for NET in "${NETWORKS[@]}"; do
    if ! docker network ls --format '{{.Name}}' | grep -q "^${NET}$"; then
      info "Creating network: $NET"
      docker network create "$NET" >/dev/null 2>&1 || err "Failed to create network: $NET"
    else
      ok "Network exists: $NET"
    fi
  done
}
# -------------------------------------------------------
# Boot Sequence (Always in the same order)
# -------------------------------------------------------
boot_core() {
  echo "🅰 Starting Core stack..."
  # --- ADDED: --env-file "$ENV_FILE" ---
  docker compose -f "$COMPOSE_CORE" --env-file "$ENV_FILE" up -d --build --remove-orphans || warn "Core stack had issues."
}
boot_main() {
  echo "🅱 Starting Main stack..."

  # 1. Explicitly build the base platform image first
  echo "🔨 Building helix-platform base image..."
  # --- ADDED: --env-file "$ENV_FILE" ---
  docker compose -f "$COMPOSE_MAIN" --env-file "$ENV_FILE" build --no-cache helix-platform || { 
    warn "Base image build failed."; 
    return 1; 
  }
  # 2. Start the rest of the services.
  echo "🚀 Starting dependent services..."
  # --- ADDED: --env-file "$ENV_FILE" ---
  docker compose -f "$COMPOSE_MAIN" --env-file "$ENV_FILE" up -d --build --remove-orphans || warn "Main stack had issues."
}
# -------------------------------------------------------
# 🥋 NEW: Unified Boot Function (One Strike) 🥋
# -------------------------------------------------------
boot_full_stack() {
  echo "🚀 Starting Full Helix Stack (Core + Main)..." 
  # 1. Build the dependent helix-platform base image first
  #    We build it against ALL compose files so it knows about 'keycloak' during the build
  echo "🔨 Building helix-platform image..."
  docker compose -f "$COMPOSE_CORE" -f "$COMPOSE_MAIN" \
    --env-file "$ENV_FILE" build helix-platform || {
      warn "Base image build failed.";
      return 1;
    }
  # 2. Start all services together using both configuration files.
  echo "🚀 Starting all services (waiting for health checks)..."
  docker compose -f "$COMPOSE_CORE" -f "$COMPOSE_MAIN" \
    --env-file "$ENV_FILE" up -d --build --remove-orphans || err "Full stack boot failed."
}
boot_llm() {
  echo "🦜 Starting LLM stack..."
  # ... (Content remains the same, LLM is separate and doesn't depend on Keycloak/Main)
  docker compose -f "$COMPOSE_LLM" --env-file "$ENV_FILE" up -d --build --remove-orphans || warn "LLM stack had issues."
}
# -------------------------------------------------------
# Execution Flow (Fixed to use the new function)
# -------------------------------------------------------
info "🚀 Helix Boot (Bruce Lee Unified Edition)"
ensure_all_networks
boot_full_stack  # Calls both Core and Main compose files together
boot_llm         # Calls the separate LLM compose file
ok "🏁 Helix platform boot complete!"
echo ""
info "To check status run:"
echo "   ./scripts/modules/helix-status-v2.sh"
echo ""