# ==========================================
# 🧠 HelixNet Makefile – Managed with Care 🧠
# ==========================================
# Purpose : Simplify Docker Compose orchestration & database management
# Author  : Sherlock (Your faithful assistant)
# Updated : 2025-10-08
# ==========================================

.ONESHELL:
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := helixnet

# Profiles for clarity
CORE_PROFILES := --profile core
APP_PROFILES  := --profile app

# Helpers for colorful output 🌈
INFO = @echo "🟦 [INFO]"
OK   = @echo "🟩 [OK]"
WARN = @echo "🟨 [WARN]"
ERR  = @echo "🟥 [ERROR]"

# ==========================================
# 🚀 MAIN TARGETS
# ==========================================

.PHONY: start
start: ## 🔥 Start all core + app services
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

.PHONY: setup
setup: migrate seed-data ## 💾 Apply migrations and seed initial data
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

# ==========================================
# 🗄️ DATABASE & MIGRATIONS
# ==========================================

.PHONY: migrate
migrate: ## 🧬 Apply Alembic migrations to latest head
	$(INFO) "Running Alembic migrations..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm helix-web-app alembic upgrade head
	$(OK) "Migrations applied successfully! 🎉"

.PHONY: revision
revision: core-up ## ✍️ Create a new Alembic migration (usage: make revision msg="Your message")
	$(INFO) "Generating new Alembic revision: $(msg)"
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm helix-web-app alembic revision --autogenerate -m "$(msg)"
	$(OK) "New revision created. Check 'migrations/versions/'. 🪶"

.PHONY: seed-data
seed-data: ## 🥕 Run the initial data seeding script (creates admin users, etc.)
	$(INFO) "Seeding initial data..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm helix-web-app python app/scripts/seed_users.py
	$(OK) "Data seeding complete! Users are ready. 👤"

.PHONY: reset-db
reset-db: ## 💣 Reset database (wipes volumes, runs fresh migrations)
	$(WARN) "⚠️ This will nuke your DB, volumes, and rebuild the stack!"
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
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm helix-web-app \
	python -c "from app.db.database import Base; import app.db.models; print(Base.metadata.tables.keys())"
	$(OK) "Table names displayed. 📖"

.PHONY: show-users
show-users: core-up ## 👤 Query and display all existing user emails
	$(INFO) "Fetching user emails from database..."
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) run --rm helix-web-app python app/scripts/show_users.py
	$(OK) "Users displayed. 📖"

.PHONY: nuke
nuke: ## 💣 Full cleanup – stop all containers, remove volumes, rebuild fresh
	$(WARN) "⚠️ Nuking everything (containers, networks, volumes)..."
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker stop $$(docker ps -aq) 2>/dev/null || true
	docker rm $$(docker ps -aq) 2>/dev/null || true
	docker volume prune -f
	$(OK) "Environment fully cleaned. You can rebuild safely! 🧩"

# ==========================================
# 🧪 TESTING
# ==========================================

.PHONY: test-unit
test-unit: ## 🧪 Run Python unit/integration tests (isolated DB, color logs, Chuck Norris mode)
	$(INFO) "Running Python tests with isolated test DB (ENV=testing)..."
	docker compose -f $(COMPOSE_FILE) $(APP_PROFILES) exec -e ENV=testing helix-web-app bash -c "\
		echo '🥋 Chuck Norris enters the test dojo...' && \
		cd /code/app/tests && \
		pytest -vv --color=yes --maxfail=1 --disable-warnings --tb=short && \
		echo '✅ All tests passed! Chuck Norris approves. 👊' || \
		( echo '💀 Tests failed. Chuck Norris is displeased. ⚡' && exit 1 )"
	$(OK) "Python test suite completed. 🧠"

.PHONY: test-auth
test-auth: ## 🔑 Run authenticated E2E API tests (login + token validation)
	$(INFO) "Running authenticated E2E API tests..."
	docker compose exec helix-web-app bash /code/app/tests/test_api.sh
	$(OK) "Authenticated API tests completed successfully. 🔐"

.PHONY: test
test: start setup test-unit test-auth ## 🧪 Full suite: start stack, seed data, run unit + E2E API tests
	$(OK) "Full test suite executed successfully! 🎯"

# ==========================================
# 🔗 LINKS
# ==========================================

.PHONY: links
links: ## 🔗 Show quick access links for local services
	@echo "\n🌐 --- HelixNet Access Links ---"
	@echo "🎁 GitHub Repo:              https://github.com/akenel/helixnet/tree/main"
	@echo "💻 WebApp Backend OpenAPI:   http://localhost:8000/docs"
	@echo "🐇 Flower UI (Celery):       http://0.0.0.0:5555/"
	@echo "📨 RabbitMQ Mgmt:            http://localhost:15672/"
	@echo "🗄️ MinIO Console:            http://0.0.0.0:9091/"
	@echo "🧠 PgAdmin UI:               http://0.0.0.0:5050/browser/"
	@echo "-----------------------------------\n"

# ==========================================
# 🕵️ HELP MENU
# ==========================================

.PHONY: help
help: ## 🕵️ Show this help menu
	@clear
	@echo "🔍 \033[1mAvailable Commands for HelixNet:\033[0m\n"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "⚙️  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo "\n💡 Example: make start   🚀"

.PHONY: dev
dev: ## 🧑‍💻 Open an interactive dev shell inside the running web container
	docker compose exec helix-web-app bash
