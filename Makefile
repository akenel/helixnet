# =======================================================
# 🧠 HelixNet Makefile – Bruce Lee Ops Edition (v3.0)
# =======================================================
.ONESHELL:
SHELL := /bin/bash
.DEFAULT_GOAL := help
# -------------------------------------------------------
# 🧩 Environment Setup
# -------------------------------------------------------
ENV_FILE ?= .env
ENV_SRC  := .env
ENV_CLEAN := .env.clean
# Compose profile support check (runs once)
COMPOSE_HAS_PROFILE := $(shell docker compose --help | grep -q -- "--profile" && echo 1 || echo 0)
COMPOSE_CMD := $(shell command -v docker-compose 2>/dev/null || command -v "docker compose" 2>/dev/null || echo "docker compose")
# Allows Make to read variables from .env during its initial parsing phase
ifneq ("$(wildcard $(ENV_FILE))","")
include $(ENV_FILE)
endif
# -------------------------------------------------------
# 📦 Compose Files and Profiles
# -------------------------------------------------------
COMPOSE_DIR     := compose
AUTH_COMPOSE    := $(COMPOSE_DIR)/auth-stack.yml
CORE_COMPOSE    := $(COMPOSE_DIR)/core-stack.yml
EDGE_COMPOSE    := $(COMPOSE_DIR)/edge-stack.yml
HELIX_COMPOSE   := $(COMPOSE_DIR)/helix-stack.yml
COMPOSE         := docker compose
AUTH_PROFILE    := --profile auth
CORE_PROFILE    := --profile core
EDGE_PROFILE    := --profile edge
HELIX_PROFILE   := --profile helix
# -------------------------------------------------------
# 🎨 Formatting & Color
# -------------------------------------------------------
RESET   := \033[0m
BOLD    := \033[1m
CYAN    := \033[36m
YELLOW  := \033[33m
MAGENTA := \033[35m
GREEN   := \033[32m
WARN    = @printf "⚠️  %s\n"
OK      = @printf "✅ %s\n"
INFO    = @printf "💬 %s\n"
FAIL    = @printf "💥 %s\n"
# -------------------------------------------------------
# ⚙️ MACROS
# -------------------------------------------------------
PROJECT_NAME=helixnet
ENV_FILE=.env
COMPOSE_CMD := $(shell command -v docker-compose 2>/dev/null || command -v "docker compose" 2>/dev/null || echo "docker compose")
# Compose profile support check (runs once)
COMPOSE_HAS_PROFILE := $(shell $(COMPOSE_CMD) --help | grep -q -- "--profile" && echo 1 || echo 0)
# -------------------------------------------------------
define HELIX_HEALTH
		while true; do
		clear
		./scripts/helix-status.sh --sort cpu
		sleep 2
		done
endef




# endef
define RUN_COMPOSE
	@if [ ! -f "$(ENV_FILE)" ]; then echo "💥 Missing $(ENV_FILE)!"; exit 1; fi; \
	echo "🧩 Loading environment from $(ENV_FILE)"; \
	set -a; grep -v '^[#[:space:]]' $(ENV_FILE) > /tmp/.env.filtered; source /tmp/.env.filtered; set +a; \
	if [ "$(COMPOSE_HAS_PROFILE)" = "1" ] && [ -n "$(PROFILE)" ]; then \
	  echo "▶️ Using Compose profile(s): $(PROFILE)"; \
	  $(COMPOSE_CMD) -p $${PROJECT_NAME:-HelixNet} \
	    -f $(AUTH_COMPOSE) -f $(CORE_COMPOSE) -f $(HELIX_COMPOSE) -f $(EDGE_COMPOSE) \
	    $(foreach p,$(PROFILE),--profile $${p}) $(1); \
	else \
	  echo "🚀 Running Compose without profiles"; \
	  $(COMPOSE_CMD) -p $${PROJECT_NAME:-HelixNet} \
	    -f $(AUTH_COMPOSE) -f $(CORE_COMPOSE) -f $(HELIX_COMPOSE) -f $(EDGE_COMPOSE) \
	    $(1); \
	fi
endef

# --- Env Loader: Exports variables for the shell recipe ---
define ENV_EXPORT
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "💥 Error: $(ENV_FILE) file not found. Cannot load environment variables."; \
		exit 1; \
	fi; \
	set -a; source $(ENV_FILE); set +a
endef
# --- Health Check Macro ---
define wait_for_health
	@echo "⏳ Waiting for $(1) to become healthy..."
	@for i in {1..24}; do \
		CID=$$(docker ps -q -f name=$(1)); \
		if [ -z "$$CID" ]; then \
			echo "❌ No running container for $(1). Dumping docker compose ps:"; \
			$(COMPOSE_CMD) ps; exit 1; \
		fi; \
		STATUS=$$(docker inspect -f '{{.State.Health.Status}}' $$CID 2>/dev/null || echo "starting"); \
		if [ "$$STATUS" = "healthy" ]; then echo "✅ $(1) is healthy!"; break; fi; \
		if [ $$i -eq 24 ]; then \
			echo "💥 Timeout waiting for $(1) health! Dumping last 20 logs:"; docker logs $$CID | tail -n 20; exit 1; \
		fi; \
		sleep 5; \
	done
endef

# --- Traefik Info (Cleaned up shell output) ---
define traefik_check_and_info
	@echo "⏳ Checking Traefik status (Assuming up after 5s)..."
	@sleep 5
	@CID=$$(docker ps -q -f name=traefik)
	if [ -z "$$CID" ]; then echo "💥 Traefik container not found!"; exit 1; fi; \
	STATUS=$$(docker inspect -f '{{.State.Status}}' $$CID); \
	if [ "$$STATUS" = "running" ]; then \
		echo "$(OK) Traefik is running!"; \
		printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"; \
		printf "$(CYAN)$(BOLD)# 🌐 Traefik Dashboard Access Information 🌐                                        #$(RESET)\n"; \
		printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"; \
		printf "  $(YELLOW)DASHBOARD URL:$(RESET) $(GREEN)https://traefik.helix.local$(RESET)\n"; \
		printf "  $(YELLOW)Container ID:$(RESET) $$CID\n"; \
		printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"; \
	else \
		echo "💥 Traefik container status: $$STATUS"; exit 1; \
	fi
endef
# --- Keycloak Info ---
define keycloak_info
	$(call ENV_EXPORT)
	@printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"
	@printf "$(CYAN)$(BOLD)# 🔐 Keycloak / Auth Stack Access Information 🔐                                   #$(RESET)\n"
	@printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"
	@printf "  $(YELLOW)Keycloak URL:$(RESET) $(GREEN)https://$(KC_HOSTNAME)/auth$(RESET)\n"
	@printf "  $(YELLOW)Admin Username:$(RESET) $(GREEN)$(KEYCLOAK_ADMIN_USER)$(RESET)\n"
	@printf "  $(YELLOW)Admin Password:$(RESET) $(GREEN)$(KEYCLOAK_ADMIN_PASSWORD)$(RESET)\n"
	@printf "  $(YELLOW)Postgres Host/DB:$(RESET) $(GREEN)$(POSTGRES_HOST)/$(POSTGRES_DB)$(RESET)\n"
	@printf "$(CYAN)$(BOLD)####################################################################################$(RESET)\n"
endef
# =======================================================
# 🧩 Core Targets
# =======================================================
.PHONY: status
status: ## 🧩 Verify required networks and environment
	$(INFO) "Running health checks..."
	$(call HELIX_HEALTH)

.PHONY: doctor
doctor: ## 🩺 Run diagnostics to verify Docker, Compose, and environment
	@echo "🩺 Running Helix Doctor..."
	@if ! command -v docker >/dev/null 2>&1; then echo "💥 Docker not installed!"; exit 1; fi
	@if ! docker info >/dev/null 2>&1; then echo "💥 Docker daemon not running!"; exit 1; fi
	@if ! command -v docker compose >/dev/null 2>&1; then echo "💥 Docker Compose plugin missing!"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "💥 Missing $(ENV_FILE)! Copy .env.example → .env"; exit 1; fi
	@echo "✅ Doctor check passed."
# =======================================================
.PHONY: preflight
preflight: ## 🧩 Verify required networks and environment
	$(INFO) "Running preflight checks..."
	$(call ENV_EXPORT)
	@for net in int_core edge_public; do \
		if ! docker network inspect $$net >/dev/null 2>&1; then \
			docker network create $$net && echo "✅ Created network: $$net"; \
		else \
			echo "ℹ️ Network $$net exists."; \
		fi; \
	done
	$(OK) "Networks verified."
# =======================================================
.PHONY: up
up: preflight ## 🚀 Bring up all stacks (auth, core, helix, edge)
	$(INFO) "Starting HelixNet stacks..."
	$(call RUN_COMPOSE, up -d --build)
	$(call wait_for_health,keycloak)
	$(call keycloak_info)
	$(call wait_for_health,helix)
	$(call traefik_check_and_info)
	$(OK) "All stacks are up and healthy!"
# =======================================================
.PHONY: down
down: ## 🛑 Bring down all stacks and remove orphans
	$(call RUN_COMPOSE, down --remove-orphans)
	$(OK) "All stacks brought down cleanly."
# =======================================================
.PHONY: restart
restart: ## 🔁 Restart a specific service (SERV=name) [PROFILE=edge]
	@if [ -z "$(SERV)" ]; \
		then echo "💥 Missing SERV arg. Usage: make restart SERV=keycloak [PROFILE=edge]"; \
		exit 1; 
	fi
	@echo "💬 Restarting service $(SERV)..."
	$(call RUN_COMPOSE, restart $(SERV))
	$(call wait_for_health,$(SERV))
	$(OK) "$(SERV) restarted successfully!"
# =======================================================
.PHONY: nuke
nuke: ## 💣 Full teardown of HelixNet (containers, volumes, networks)
	@echo "💥 Nuking HelixNet — full reset incoming..."
	@$(call RUN_COMPOSE,down -v --remove-orphans)
	@echo "🧹 Removing old networks..."
	@docker network rm auth_net core_net int_core edge_public 2>/dev/null || true
	@echo "🧼 Pruning any unused Docker data..."
	@docker system prune -af --volumes
	@echo "🌐 Recreating core networks..."
	@docker network create int_core || true
	@docker network create edge_public || true
	@echo "✅ Networks ready:"
	@docker network ls | grep -E "int_core|edge_public" || true
	@echo "🚀 Running preflight checks..."
	@$(MAKE) preflight
	@echo "🔧 Bringing stacks up cleanly..."
	@$(MAKE) up

# =======================================================
.PHONY: env-clean
env-clean: ## 🧼 Clean and deduplicate .env file
	@echo "🧼 Cleaning and sorting environment file..."
	@if [ ! -f $(ENV_SRC) ]; then echo "❌ No $(ENV_SRC) found!"; exit 1; fi
	@grep -vE '^\s*#' $(ENV_SRC) | grep -vE '^\s*$$' | awk -F= '!seen[$$1]++' | sort > $(ENV_CLEAN)
	@echo "✅ Clean .env written to $(ENV_CLEAN)"
# =======================================================
# 🧭 Help Menu
# =======================================================
.PHONY: help
help: ## 📘 Show all available commands
	@printf "\n${CYAN}${BOLD}HelixNet – Bruce Lee Ops Edition 🥋${RESET}\n"
	@printf "───────────────────────────────────────────────\n"
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = "##"}; {gsub(/^[ \t]+|[ \t]+$$/, "", $$2); printf "  \033[36mmake %-20s\033[0m %s\n", $$1, $$2}'
	@printf "───────────────────────────────────────────────\n"
	@printf "💡 Example: make restart SERV=keycloak\n"