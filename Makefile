# ===================================================================
# HelixNet Core Makefile - Bruce Lee Edition
# "Be water, my friend" - Simple, Fast, No Bloat
# ===================================================================
SHELL := /bin/bash
.ONESHELL:
.PHONY: help up core-up main-up llm-up down status lazy clean nuke nuke-all logs links

# --- Environment Configuration ---
SCRIPTS_DIR := scripts
MODULES_DIR := $(SCRIPTS_DIR)/modules
COMPOSE_CORE := compose/helix-core/core-stack.yml
COMPOSE_MAIN := compose/helix-main/main-stack.yml
COMPOSE_LLM := compose/helix-llm/llm-stack.yml

# --- Default Target ---
help:
	@echo ""
	@echo "===================================================================="
	@echo " HelixNet Makefile - Bruce Lee Edition"
	@echo "===================================================================="
	@echo ""
	@echo " Boot Operations:"
	@echo "  make up          | Full Stack (Core + Main + LLM)"
	@echo "  make core-up     | Stage A: Postgres, Traefik, Redis, Keycloak"
	@echo "  make main-up     | Stage B: Helix API, Workers, Beat"
	@echo "  make llm-up      | Stage C: Ollama, OpenWebUI"
	@echo ""
	@echo " Utilities:"
	@echo "  make status      | TUI Status Dashboard"
	@echo "  make lazy        | Lazydocker UI"
	@echo "  make logs        | Stream helix-platform logs"
	@echo "  make links       | Show access URLs"
	@echo ""
	@echo " Backup & Restore:"
	@echo "  make backup           | Full backup (postgres, keycloak, minio)"
	@echo "  make backup-postgres  | Backup PostgreSQL only"
	@echo "  make backup-list      | List available backups"
	@echo "  make backup-config    | Show backup configuration"
	@echo "  make restore BACKUP=X | Restore from backup ID (or 'latest')"
	@echo ""
	@echo " Cleanup:"
	@echo "  make down        | Stop all containers"
	@echo "  make clean       | Stop + prune dangling"
	@echo "  make nuke        | Safe reset (keeps DB, models, certs)"
	@echo "  make nuke-all    | DESTROY EVERYTHING (fresh start)"
	@echo ""

# ===================================================================
# BOOT OPERATIONS
# ===================================================================

up:
	@echo "Booting Full Helix Stack..."
	@bash scripts/helix-boot.sh

core-up:
	@echo "Starting Core Stack (Postgres, Traefik, Redis, Keycloak)..."
	@docker compose -f $(COMPOSE_CORE) up -d --build

main-up:
	@echo "Starting Main Stack (API, Workers, Beat)..."
	@docker compose -f $(COMPOSE_CORE) -f $(COMPOSE_MAIN) up -d --build

llm-up:
	@echo "Starting LLM Stack (Ollama, OpenWebUI)..."
	@docker compose -f $(COMPOSE_LLM) up -d

# ===================================================================
# UTILITIES
# ===================================================================

status:
	@./scripts/modules/helix-status-v3.0.1.sh

lazy:
	@command -v lazydocker >/dev/null 2>&1 || { echo "Error: lazydocker not installed"; exit 1; }
	@lazydocker

logs:
	@docker logs helix-platform -f 2>/dev/null || echo "Container 'helix-platform' not running"

links:
	@echo ""
	@echo "=== HelixNet Access URLs ==="
	@echo "POS:         https://helix-platform.local/pos"
	@echo "API Docs:    https://helix-platform.local/docs"
	@echo "Keycloak:    https://keycloak.helix.local"
	@echo "Traefik:     https://traefik.helix.local"
	@echo "Dozzle:      https://dozzle.helix.local"
	@echo "MailHog:     https://mailhog.helix.local"
	@echo "Flower:      https://flower.helix.local"
	@echo ""

# ===================================================================
# BACKUP & RESTORE OPERATIONS
# ===================================================================

backup:
	@bash scripts/modules/tools/helix-backup.sh all

backup-postgres:
	@bash scripts/modules/tools/helix-backup.sh postgres

backup-keycloak:
	@bash scripts/modules/tools/helix-backup.sh keycloak

backup-minio:
	@bash scripts/modules/tools/helix-backup.sh minio

backup-all:
	@bash scripts/modules/tools/helix-backup.sh all

backup-list:
	@bash scripts/modules/tools/helix-backup.sh list

backup-config:
	@bash scripts/modules/tools/helix-backup.sh config

restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make restore BACKUP=<backup_id>"; \
		echo "       make restore BACKUP=latest"; \
		bash scripts/modules/tools/helix-restore.sh list; \
	else \
		bash scripts/modules/tools/helix-restore.sh $(BACKUP); \
	fi

restore-postgres:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make restore-postgres BACKUP=<backup_id>"; \
	else \
		bash scripts/modules/tools/helix-restore.sh $(BACKUP) postgres; \
	fi

restore-verify:
	@bash scripts/modules/tools/helix-restore.sh verify $(BACKUP)

# ===================================================================
# CLEANUP OPERATIONS
# ===================================================================

down:
	@echo "Stopping all Helix containers..."
	@docker compose -f $(COMPOSE_CORE) -f $(COMPOSE_MAIN) down 2>/dev/null || true
	@docker compose -f $(COMPOSE_LLM) down 2>/dev/null || true

clean:
	@echo "Soft cleanup (stop + prune dangling)..."
	@$(MAKE) down
	@docker system prune -f

# Safe nuke - keeps persistent data (DB, Ollama models, certs)
nuke:
	@echo ""
	@echo "=== SAFE NUKE: Resetting runtime (keeping DB, models, certs) ==="
	@echo ""
	@docker compose -f $(COMPOSE_CORE) -f $(COMPOSE_MAIN) down --remove-orphans 2>/dev/null || true
	@docker compose -f $(COMPOSE_LLM) down --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo ""
	@echo "Safe nuke complete. Persistent data preserved."
	@echo "Run 'make up' to restart."
	@echo ""

# Full destruction - removes EVERYTHING for fresh wizard install
nuke-all:
	@echo ""
	@echo "============================================================"
	@echo " FULL DESTRUCTION MODE"
	@echo " This will DELETE:"
	@echo "   - All containers and volumes"
	@echo "   - Postgres data, Keycloak realms"
	@echo "   - All helix images"
	@echo "============================================================"
	@echo ""
	@read -p "Type 'DESTROY' to confirm: " confirm && [ "$$confirm" = "DESTROY" ] || { echo "Aborted."; exit 1; }
	@echo ""
	@echo "Stopping all containers..."
	@docker compose -f $(COMPOSE_CORE) -f $(COMPOSE_MAIN) down --volumes --remove-orphans 2>/dev/null || true
	@docker compose -f $(COMPOSE_LLM) down --volumes --remove-orphans 2>/dev/null || true
	@echo "Removing helix images..."
	@docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^helix' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "Pruning system..."
	@docker system prune --volumes -f
	@echo "Recreating networks..."
	@docker network create helixnet_core 2>/dev/null || true
	@docker network create helixnet_edge 2>/dev/null || true
	@echo ""
	@echo "============================================================"
	@echo " DESTRUCTION COMPLETE"
	@echo " Run 'make up' for fresh install (realms auto-import)"
	@echo "============================================================"
	@echo ""
