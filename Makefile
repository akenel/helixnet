# =======================================================
# 🧠 HelixNet Makefile – The Professional Standard 🧠
# =======================================================
# Purpose : Simplified, descriptive orchestration for Docker Compose
# Author  : Gemini, your development partner and Angel the fixer
# Updated : 2025-10-19 v0.0.2
# =======================================================
.ONESHELL:
SHELL := /bin/bash
include .env
COMPOSE_FILE := docker-compose.yml
PROJECT_NAME := helixnet
DB_NAME := postgres
DB_USER := postgres

# --- Profiles & Variables (KIC KIS) ---
CORE_PROFILES := --profile core
APP_PROFILES  := --profile app
WEB_SERVICE   := helix-web-app
# --- Emoji Helpers (The Chuck Standard) ---
# Main States
START = @echo "🟢 [INIT] Starting up the engines..."
STOP  = @echo "🔴 [SHUTDOWN] Ceasing operations..."
DONE  = @echo "✨ [COMPLETE] Task finished successfully."
WARN  = @echo "⚠️  [ATTENTION] Proceed with caution."
FAIL  = @echo "❌ [FAILURE] Something went wrong."
# Actions
DB    = @echo "💾 [DATABASE] "
CODE  = @echo "💻 [CODEBASE] "
TEST  = @echo "🧪 [TESTING] "
BUILD = @echo "🏗️  [BUILDING] "
CLEAN = @echo "🧹 [CLEANUP] "
# =======================================================
# 🚀 1. LIFECYCLE MANAGEMENT (Full Stack)
# =======================================================
.PHONY: up
up: build ## ⬆️  Bring the entire stack up (Builds images first if necessary)
	$(START) "Starting ALL containers in detached mode..."
	set -a; . ./.env; set +a; docker compose -f $(COMPOSE_FILE) up -d --remove-orphans
	$(DONE) "HelixNet is LIVE! Access links via 'make links'. 🌐"

.PHONY: down
down: ## ⬇️  Stop and remove all containers (Keeps data volumes)
	$(STOP) "Stopping and gracefully removing ALL services..."
	set -a; . ./.env; set +a; docker compose -f $(COMPOSE_FILE) down
	$(DONE) "All containers are stopped and gone. They'll be back. 😉"

.PHONY: build
build: ## 🏗️  Build all Docker images from their latest source
	$(BUILD) "Re-compiling Docker images for Core and App services..."
	docker compose -f $(COMPOSE_FILE) build
	$(DONE) "All images built successfully! ✅"

.PHONY: rebuild
rebuild: ## 🔄 Stop, rebuild, and start everything fresh
	$(CODE) "Executing full environment reset and rebuild (down -> build -> up)..."
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up
	$(DONE) "Full rebuild completed! We are running on fresh code and containers. 🧩"
# =======================================================
# ⚙️ 2. INFRASTRUCTURE & CODE DEPLOY
# =======================================================
.PHONY: core-up
core-up: ## 🧱 Start only core infra (DB, Redis, Broker, MinIO)
	$(DB) "Starting essential core infrastructure services..."
	set -a; . ./.env; set +a; \
	# 1. Start ALL containers quickly (NO WAITING HERE)
	docker compose -f $(COMPOSE_FILE) $(CORE_PROFILES) up -d --remove-orphans # added --remove-orphans here too
	@echo "🧱 [CORE UP] Core services started (may not be fully healthy yet). Moving to check."
# =======================================================
.PHONY: code-deploy
code-deploy: ## 📦 Build new code images and restart web/workers (Fast update)
	$(CODE) "Building new application images (Web, Worker, Beat) to grab latest code..."
	docker compose -f $(COMPOSE_FILE) $(APP_PROFILES) build
	$(CODE) "Restarting application services using the newly built images..."
	docker compose -f $(COMPOSE_FILE) $(APP_PROFILES) up -d --remove-orphans
	$(DONE) "New code is deployed and application services are running. 🥳"
# =======================================================
# 🗄️ 3. DATABASE MANAGEMENT
# =======================================================
.PHONY: setup
setup: migrate seed ## 💾 Complete initial setup (migrate, then seed)
	$(DB) "Initial application setup complete! Ready to accept requests. 🚀"
# =======================================================
.PHONY: migrate
migrate: core-up ## 🧬 Apply Alembic migrations to the database head
	$(DB) "Applying new database migrations to the latest head..."
	docker compose run --rm $(WEB_SERVICE) alembic upgrade head
	$(DONE) "Migrations applied successfully! Database schema is up-to-date. 🎉"
# =======================================================
.PHONY: rev
rev: core-up ## ✍️ Create a new Alembic migration (usage: make rev msg="Your description")
	$(DB) "Generating new Alembic revision: $(msg)..."
	docker compose run --rm $(WEB_SERVICE) alembic revision --autogenerate -m "$(msg)"
	$(DONE) "New revision created. Check 'migrations/versions/' folder. 🪶"
# =======================================================
.PHONY: seed
seed: core-up ## 🥕 Run the initial data seeding script (admin user creation, etc.)
	$(DB) "Executing initial data seeding script..."
	# 🌍 KEYCLOAK REALM IMPORT: THE BRUCE LEE PRECISION STRIKE 🐉
	@echo "🌍 [KEYCLOAK] Attempting realm 'helixnet' import..."
	docker exec keycloak /opt/keycloak/bin/kc.sh import \
		--file /opt/keycloak/data/import/helix-realm.json \
		--realm helixnet

	@echo "✅ Realm import attempt finished. Checking status..."
	# The 'make' process will halt here if the command above returned an error code.
		
	# 🔑 Next, run the user seeding script (SPRINT 2/3)
	docker compose run --rm $(WEB_SERVICE) python app/scripts/seed_users.py
	$(DONE) "Data seeding complete! Users and base data are ready. 👤"

.PHONY: db-nuke
db-nuke: ## 💥 Nuke DB (Stop, remove volumes, restart core, migrate, seed)
	$(WARN) "🚨 DANGER ZONE: This will wipe ALL database volumes and data!"
	$(CLEAN) "Removing all volumes associated with the stack..."
	# 1. 🧹 CLEAN UP: Stop, remove containers/volumes, and remove orphans.
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans # ADDED --remove-orphans
	# 2. 💾 START: Call core-up to start all containers (now non-blocking)
	$(DB) "Restarting core services and starting Keycloak..."
	$(MAKE) core-up
	# 3. 🥋 HEALTH CHECK (Postgres First - Essential for Keycloak Startup)
	@echo "⏳ [WAITING] Waiting for Postgres to be fully ready..."
	docker compose wait postgres
	# 4. 🐉 HEALTH CHECK (Keycloak Full Provisioning)
	@echo "💾 [DATABASE] Waiting for Keycloak fully provisioned check... (API /certs ready) 🚀"
	# This loop WILL stop hanging now because the container is running and Postgres is ready.
	while ! docker exec keycloak curl -fL http://keycloak:8080/realms/master/protocol/openid-connect/certs > /dev/null 2>&1; do sleep 3; done
	$(DONE) "Core infra successfully rebuilt and ready! 💯"
	$(MAKE) show # Run DB migrations
	$(DONE) "Full db-nuke and setup completed. Ready for development. 🎉"
# =======================================================
# 🧰 4. UTILITIES & ACCESS
# =======================================================
.PHONY: logs
logs: ## 📜 Tail logs from all running containers
	@echo "👁️  [LOGS] Tailing logs... (Ctrl+C to stop)"
	docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: shell
shell: ## 🧑‍💻 Open an interactive BASH shell inside the main web container
	@echo "🦪 [SHELL] Opening BASH inside the $(WEB_SERVICE) container..."
	docker compose exec $(WEB_SERVICE) bash

.PHONY: python
python: ## 🐍 Open an interactive PYTHON shell inside the main web container
	@echo "🐍 [PYTHON] Opening interactive Python environment..."
	docker compose exec $(WEB_SERVICE) python

.PHONY: tables
tables: core-up ## 🧾 Show all SQLAlchemy table names from Base.metadata
	$(DB) "Fetching table names from SQLAlchemy Base metadata..."
	docker compose run --rm $(WEB_SERVICE) 
	python -c "from app.db.database import Base; import app.db.models; print(Base.metadata.tables.keys())"
	$(DONE) "Table names displayed for inspection. 📖"

.PHONY: users
users: core-up ## 👤 Query and display all existing user emails
	$(DB) "Fetching all user emails from the database..."
	docker compose run --rm $(WEB_SERVICE) python app/scripts/show_users.py
	$(DONE) "User list retrieved. 👥"

.PHONY: portly
portly: ## 🖥️  Quick restart for Portainer management UI
	$(STOP) "Stopping Portainer..."
	docker compose stop portainer
	$(START) "Starting Portainer..."
	docker compose start portainer
	$(DONE) "Portainer is ready! Access here: https://portainer.helix.local/ 💥"

.PHONY: links
links: ## 🔗 Show quick access links for local services
	@echo "\n🌐 --- HelixNet Access Links ---"
	@echo "🎁 GitHub Repo:              https://github.com/akenel/helixnet/tree/main"
	@echo "💻 WebApp Backend OpenAPI:   http://helix.local/docs"
	@echo "🐇 Flower UI (Celery):       http://0.0.0.0:5555/"
	@echo "📨 RabbitMQ Mgmt:            http://localhost:15672/"
	@echo "🗄️ MinIO Console:            http://0.0.0.0:9091/"
	@echo "🧠 PgAdmin UI:               http://0.0.0.0:5050/browser/"
	@echo "-----------------------------------\n"
# =======================================================
# 🧪 5. TESTING SUITE
# =======================================================
.PHONY: test-unit
test-unit: ## 🧪 Run Python unit/integration tests (isolated DB)
	$(TEST) "Running Python unit tests with isolated test DB (ENV=testing)..."
	docker compose exec -e ENV=testing $(WEB_SERVICE) bash -c "
	echo '🥋 Chuck Norris enters the test dojo...' && 
	cd /code/app/tests && 
	pytest -vv --color=yes --maxfail=1 --disable-warnings --tb=short && 
	echo '✅ All tests passed! Chuck Norris approves. 👊' || 
	( echo '💀 Tests failed. Chuck Norris is displeased. ⚡' && exit 1 )"
	$(DONE) "Unit test suite completed. 🧠"

.PHONY: test-e2e
test-e2e: ## 🔑 Run authenticated E2E API tests (login + token validation)
	$(TEST) "Running authenticated End-to-End API tests (E2E)..."
	docker compose exec $(WEB_SERVICE) bash /code/app/tests/test_api.sh
	$(DONE) "E2E API tests completed successfully. 🔐"

.PHONY: test
test: up setup test-unit test-e2e ## 🎯 Full test suite: start, setup, run unit + E2E
	$(DONE) "The full HelixNet test suite has executed successfully! Everything is green. 🥇"

.PHONY: smoke
smoke: ## 💨 Run the helix-super-smoke quick health check
	$(TEST) "Running quick smoke test script..."
	docker compose exec $(WEB_SERVICE) bash app/scripts/helix-super-smoke.sh
	$(DONE) "Smoke test successful. Health check passed. 💨"

# =======================================================
# 🕵️ 6. HELP MENU
# =======================================================
.PHONY: help
help: ## ❓ Show this descriptive help menu
	@clear
	@echo "🔍 \033[1mAvailable Commands for HelixNet:\033[0m\n"]]
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = "##"}; \
	{ \
	cmd=$$1; \
	sub(/^.*Makefile:/, "", cmd); \
	gsub(/:.*/, "", cmd); \
	printf "%s\t\033[36m make %-20s\033[0m\n", $$2, cmd \
	}'
	@echo "  💡 Example: make up && make setup   🚀"	
	@echo "                                                make up && make setup"

.PHONY: show-tables
show-tables: core-up ## 📊 List all tables in the public schema and their owners
	@echo "========================================"
	@echo "📂 DATABASE TABLES (DB: $(DB_NAME))"
	@echo "========================================"
	docker-compose exec db psql -d $(DB_NAME) -U $(DB_USER) -c '\dt'

.PHONY: show-users
show-users: core-up ## 👤 Display schema (\d+) and data (SELECT *) for the 'user' table
	@echo "\n========================================"
	@echo "👤 USER TABLE SCHEMA (Table: public.user)"
	@echo "========================================"
	docker-compose exec db psql -d $(DB_NAME) -U $(DB_USER) -c '\d+ user'
	@echo "\n========================================"
	@echo "👥 USER TABLE DATA (SELECT * FROM user)"
	@echo "========================================"
	docker-compose exec db psql -d $(DB_NAME) -U $(DB_USER) -c 'SELECT * FROM public.user;'

.PHONY: show
show: show-tables show-users ## 🎯 Consolidated command: Show all DB inspection data (tables + users)
	@echo "\n========================================"
	@echo "✅ DB inspection complete."
	@echo "========================================\n"

.PHONY: db-backup
db-backup: ## 🧩 Create a timestamped backup of the current database (before nuking)
	$(DB) "Creating a timestamped backup of $(DB_NAME)..."
	mkdir -p backups
	docker compose exec db pg_dump -U $(DB_USER) $(DB_NAME) > backups/backup_$$(date +%F_%H%M).sql
	$(DONE) "Backup created successfully in the ./backups directory. 💾"

.PHONY: rebuild-timed
rebuild-timed: ## ⏱️  Time and log a full nuke → rebuild → setup cycle
	$(CODE) "Executing timed rebuild sequence (db-nuke → build → up → setup)..."
	(time (make db-nuke && make build && make up && make setup)) 2>&1 | tee rebuild_$(date +%F_%H%M).log
	$(DONE) "Timed rebuild completed. Logs saved to ./rebuild_*.log 📊"

.PHONY: wait-for-health
wait-for-health: ## Wait for critical services (postgres, keycloak) to become healthy
	@echo "⏳ [WAITING] Waiting for Postgres and Keycloak to reach 'healthy' state..."
	docker compose wait postgres keycloak 
	$(DONE) "Critical services are Healthy."

.PHONY: kc-token
kc-token: ## 🔑 Retrieve and test the Keycloak Admin Access Token (for verification)
	@echo "🔑 [KEYCLOAK] Testing kcadm.sh connection and fetching Admin Token..."
	docker exec keycloak /opt/keycloak/bin/kcadm.sh config credentials \
		--server http://localhost:8080/ \
		--realm master \
		--user ${KC_BOOTSTRAP_ADMIN_USERNAME} \
		--password ${KC_BOOTSTRAP_ADMIN_PASSWORD} \
		--client admin-cli > /dev/null 2>&1
	@echo "✅ Credentials configured successfully (master realm)."
	@echo "⏳ Checking if helixnet-api client exists in 'helixnet' realm..."
	docker exec keycloak /opt/keycloak/bin/kcadm.sh get clients -r helixnet \
		--query clientId=helixnet-api
	@echo "✨ [COMPLETE] Keycloak CLI tool is configured and connected to the 'helixnet' realm."

.PHONY: toke
toke: ## 🔑 Retrieve and display a decoded Keycloak Admin token (QA Proof)
	@echo "🔑 [KEYCLOAK] Retrieving and decoding Admin Token for Chuck & Bruce..."
	@docker exec helix-web-app python /code/app/scripts/get_admin_token.py
	@echo "✨ [COMPLETE] Keycloak token proof generated."

# .PHONY: seed
# seed: db-upgrade ## 💾 Perform initial data seeding (USERS, ROLES, etc.)
# 	@echo "💾 [DATABASE] Executing initial data seeding script..."
# 	@docker exec helix-web-app python /code/app/scripts/seed_users.py
# 	@echo "✨ [COMPLETE] Task finished successfully. Data seeding complete! Users and base data are ready. 👤"