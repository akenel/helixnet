# ===================================================================
# 🌊 HelixNet Core Makefile - Bruce Lee Edition (Lazydocker Integrated)
# Provides simple, TUI, and full CLI targets for Docker-Compose ops.
# ===================================================================
# Use bash for better script compatibility
SHELL := /bin/bash
.ONESHELL:
.PHONY: help up core-up main-up llm-up down status lazy clean nuke logs links

# --- Environment Configuration ---
SCRIPTS_DIR := scripts
MODULES_DIR := $(SCRIPTS_DIR)/modules

# --- Default Target ---
help:
	@echo ""
	@echo "===================================================================="
	@echo " 🥋 HelixNet Makefile - Core Operations (Bruce Lee Style) 🥋"
	@echo "===================================================================="
	@echo "  Use flags like 'DRY_RUN=true make up' to test commands."
	@echo ""
	@echo " 🚀 Boot/Start Operations:"
	@echo "  make up          | Boots the Full Stack (Core -> Main -> LLM)"
	@echo "  make core-up     | Boots Stage 🅰: Postgres, Traefik, Redis, etc."
	@echo "  make main-up     | Boots Stage 🅱: Helix API, Workers, Beat (Requires Core)"
	@echo "  make llm-up      | Boots Stage 🦜: Ollama, OpenWebUI (Requires Core)"
	@echo ""
	@echo " 🩺 Utility & Dashboards:"
	@echo "  make status      | Runs the custom 📊 Helix TUI Status Dashboard"
	@echo "  make lazy        | Runs 🖥️  Lazydocker (Full terminal-based Docker UI)"
	@echo "  make links       | Shows quick access URLs (e.g., Traefik, Grafana)"
	@echo "  make logs        | Streams logs for the main 'helix' API container"
	@echo ""
	@echo " 💥 Teardown & Cleanup:"
	@echo "  make down        | Gracefully stops all running Helix containers"
	@echo "  make clean       | Soft cleanup: stops all, removes dangling resources"
	@echo "  make nuke        | Deep cleanup: stops all, prunes volumes, and removes images (DANGEROUS)"
	@echo ""

prune:
	@echo "--- 🦜 Starting Helix PRUNE ---"
	docker system prune -a --volumes

# --- Boot Flow ---

llm-up:
	@echo "--- 🦜 Starting Helix LLM Stack ---"
	@NO_GUM=true bash $(MODULES_DIR)/helix-ollama.sh up
# --- Boot Flow ---
up:
	@echo "🚀 Booting Full Helix Stack..."
	# 🚩 FIX: This now executes the new script that merges Core and Main
	@bash scripts/helix-boot.sh 

# OLD TARGETS (These are now redundant or need to be rewritten to use the new logic if you still need them):
core-up:
	@echo "--- 🅰 Starting Helix Core Stack ---"
 	   @NO_GUM=true bash -x $(MODULES_DIR)/helix-boot-core.sh # This likely calls the old, separate logic
	# You should probably replace the content of helix-boot-core.sh to only run Core services.

main-up:
	@echo "--- 🅱 Starting Helix Main Stack ---"
	@NO_GUM=true bash $(MODULES_DIR)/helix-boot-main.sh # This will FAIL unless rewritten
# -------------------------------------------------------------------
# --- Utility & Status ---
# -------------------------------------------------------------------

dr-demo:
	@echo "# Show normal operation"
	@echo "# Add to your .bashrc for DEMO MODE terminal"
	export PS1="\e[41mDEMO MODE\e[0m \u@\h:\w\$ "
	./scripts/modules/tools/helix-backup-demo.sh
	@echo "# Simulate disaster"
	./scripts/modules/tools/helix-disaster-demo.sh
	@echo "# Demonstrate "recovery" from USB"
	cd /mnt/usb/velix-demo/latest
	./restore-demo.sh

status:
	@echo "--- 📊 Running Custom Helix TUI Status Check ---"
	./scripts/modules/helix-status-v3.0.1.sh

lazy:
	@echo "--- 🖥️ Launching Lazydocker UI ---"
	@command -v lazydocker >/dev/null 2>&1 || { echo >&2 "Error: lazydocker is not installed. Please install it to use this target."; exit 1; }
	lazydocker

links:
	@echo "--- 🔗 Quick Access Links ---"
	@echo "API Docs:    https://helix-platform.local/docs"
	@echo "Traefik:     https://traefik.helix.local/dashboard/"
	@echo "Grafana:     https://grafana.helix.local"
	@echo "OpenWebUI:   http://openwebui.helix.local"
	@echo "Dozzle Logs: https://dozzle.helix.local"

logs:
	@echo "--- 📜 Streaming Helix API Logs (CTRL+C to exit) ---"
	@docker logs helix -f || echo "Container 'helix' is not running."

# -------------------------------------------------------------------
# --- Teardown & Cleanup ---
# -------------------------------------------------------------------

down:
	@echo "--- 🛑 Stopping all Helix containers ---"
	@bash $(MODULES_DIR)/helix-down.sh

clean:
	@echo "--- 🧹 Soft Cleanup (Stop + Prune dangling resources) ---"
	@bash $(MODULES_DIR)/reset_docker.sh -d

nuke:
	@echo "--- 💥 DANGER: Deep Cleanup (Stop, Prune Volumes, Remove Images) ---"
	@bash $(MODULES_DIR)/helix-reset-cleaner.sh