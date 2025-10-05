# ==========================================
# 🧠 HelixNet Makefile – Managed with Care 🧠
# ==========================================
# Purpose: Simplify Docker Compose orchestration & database management
# Author: Sherlock (Your faithful assistant)
# Updated: 2025-10-05
# ==========================================
# 🧩 VARIABLES

COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := helixnet
# Profiles - Defined for clear command composition

CORE_PROFILES := --profile core
APP_PROFILES := --profile app
# Helpers for colorful output 🌈

INFO  = @echo "🟦 [INFO] "
OK    = @echo "🟩 [OK] "
WARN  = @echo "🟨 [WARN] "
ERR   = @echo "🟥 [ERROR] "
# ==========================================
# 🚀 MAIN TARGETS
# ==========================================

.PHONY: start
start: ## 🔥 Start all core + app services (Web, Worker, DBs, etc.)
	$(INFO) "Starting HelixNet stack..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) $(APP_PROFILES) up -d
	$(OK) "All services are up and running! 🚀"

.PHONY: stop
stop: ## 🧯 Stop and remove all containers
	$(INFO) "Stopping and cleaning up containers..."
	docker compose -f $(COMPOSE_FILE) down
	$(OK) "Containers stopped and removed. 🧹"

.PHONY: build
build: ## 🛠️ Build all Docker images
	$(INFO) "Building Docker images..."
	docker compose -f $(COMPOSE_FILE) build
	$(OK) "Build complete! ✅"

.PHONY: rebuild
rebuild: ## 🔄 Stop, rebuild, and start everything fresh
	$(INFO) "Rebuilding full environment..."
	$(MAKE) stop
	$(MAKE) build
	$(MAKE) start
	$(OK) "Full rebuild completed! 🧩"
# --- POST-BUILD / SETUP ---

.PHONY: setup
setup: migrate seed-data ## 💾 Runs ALL post-build commands: Migrates DB then seeds initial user.
	$(OK) "Application setup complete! Ready to rock. 🚀"
# ==========================================
# ⚙️ CORE SERVICES
# ==========================================

.PHONY: core-up
core-up: ## 🧱 Start only core services (DB, cache, broker, storage)
	$(INFO) "Starting core infrastructure..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) up -d
	$(OK) "Core services are up. 💾"

.PHONY: logs
logs: ## 📜 Tail logs from all running containers
	$(INFO) "Tailing logs... (Ctrl+C to exit)"
	docker compose -f $(COMPOSE_FILE) logs -f
# 	==========================================
# 	🗄️ DATABASE & MIGRATIONS
# 	==========================================

.PHONY: migrate
migrate: ## 🧬 Apply Alembic migrations to latest head
	$(INFO) "Running Alembic migrations..."
# FIX: Use CORE_PROFILES to ensure Postgres is available without triggering unnecessary dependencies
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm web alembic upgrade head
	$(OK) "Migrations applied successfully! 🎉"

.PHONY: revision
revision: core-up ## ✍️ Create a new Alembic migration (usage: make revision msg="Your message")
	$(INFO) "Generating new Alembic revision: $(msg)"
# NOTE: Core services must be up first (make core-up) for autogenerate to inspect the database.
	docker compose -f $(COMPOSE_FILE) (COREP​ROFILES)run−−rmwebalembicrevision−−autogenerate−m"(msg)"
	$(OK) "New revision created. Check 'migrations/versions/'. 🪶"

.PHONY: seed-data
seed-data: ## 🥕 Run the initial data seeding script (creates admin users, etc.)
	$(INFO) "Seeding initial data..."
# Only core profile needed for DB access
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm web python app/scripts/seed_users.py
	$(OK) "Data seeding complete! Users are ready. 👤"

.PHONY: reset-db
reset-db: ## 💣 Reset database (wipes volumes, runs fresh migrations)
	$(WARN) "⚠️  This will nuke your DB, volumes, and rebuild the stack!"
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) up -d
	docker compose -f $(COMPOSE_FILE) $(APP_PROFILES) build
	$(MAKE) migrate
	$(OK) "Database reset and migrated. 🧩"
# ==========================================
# 🧰 UTILITIES
# ==========================================

.PHONY: show-tables
show-tables: ## 🧾 Show all SQLAlchemy table names from Base.metadata
	$(INFO) "Fetching table names from database..."
# Must use CORE_PROFILES to ensure Postgres is running.
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm web 

	python -c "from app.db.database import Base; import app.db.models; print(Base.metadata.tables.keys())"
	$(OK) "Table names displayed. 📖"

.PHONY: test
test: ## 🧪 Run pytest inside the web container
	$(INFO) "Running tests..."
# Note: This command requires the web service to be ALREADY running with make start
	docker compose exec web pytest app/tests/ -v
	$(OK) "All tests completed. 🧪"

.PHONY: links
links: ## 🔗 Show quick access links for local services
	@echo "\n🌐 --- HelixNet Access Links ---"
	@echo "🎁️ GitHub Repo:         https://github.com/akenel/helixnet/tree/main#"
	@echo "💻 WebApp Backend OpenApi:   http://localhost:8000/docs (Auth details from seeded users)"
	@echo "🐇 Flower UI (Celery):   http://0.0.0.0:5555/"
	@echo "📨 RabbitMQ Mgmt:        http://localhost:15672 (User/Pass from .env)"
	@echo "🗄️  MinIO Console:      http://0.0.0.0:9091 (User/Pass from .env)"
	@echo "🧠 PgAdmin UI 🐘 Postgres:   http://0.0.0.0:5050/browser/ (User/Pass for 'helix_db' from .env)"
	@echo "-----------------------------------\n"
# ==========================================
# 💡 HELP MENU (THE CROWN JEWEL)
# ==========================================

.PHONY: help
help: ## 🕵️ Show this help menu
	@clear
	@echo "🔍 \033[1mAvailable Commands for HelixNet:\033[0m\n"
	@grep -E '^[a-zA-Z_-]+:.##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.##"}; {printf "⚙️  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo "\n💡 Example: make start   🚀"

.PHONY: show-users
show-users: core-up ## 👤 Query and display all existing user emails
	$(INFO) "Fetching user emails from database..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm web python app/scripts/show_users.py
	$(OK) "Users displayed. 📖"
