# ===================================================================
# HelixNet Core Makefile - Bruce Lee Edition
# "Be water, my friend" - Simple, Fast, No Bloat
# ===================================================================
SHELL := /bin/bash
.ONESHELL:
.PHONY: help up core-up main-up llm-up test down status lazy clean nuke nuke-all logs links

# --- Environment Configuration ---
SCRIPTS_DIR := scripts
MODULES_DIR := $(SCRIPTS_DIR)/modules
COMPOSE_CORE := compose/helix-core/core-stack.yml
COMPOSE_MAIN := compose/helix-main/main-stack.yml
COMPOSE_LLM := compose/helix-llm/llm-stack.yml
TEST_SVC := helix-platform

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
	@echo " Testing:"
	@echo "  make test        | Run pytest inside helix-platform (the real app env)"
	@echo "  make test PYTEST_ARGS='-k llm'  | Pass extra args to pytest"
	@echo ""
	@echo " 🦁 LEO (Watch the Lion Work):"
	@echo "  make leo         | Real-time git monitor (2s refresh)"
	@echo "  make watch-leo   | Same as 'make leo'"
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
# TESTING
# ===================================================================
# Tests run INSIDE the helix-platform container -- the real app env (fastapi,
# full config, email-validator). The .venv on the host is the aux toolbox (no
# fastapi), so host pytest can't run the full suite. Code is bind-mounted
# (../../src:/app/src), so this always tests the live tree. pyproject.toml is
# NOT mounted, so we pass -o asyncio_mode=auto on the CLI. pytest deps are
# installed on first run (image stays lean -- no test deps baked into prod).
test:
	@docker ps --format '{{.Names}}' | grep -q '^$(TEST_SVC)$$' || { echo "❌ $(TEST_SVC) not running -- run 'make up' first"; exit 1; }
	@echo "🧪 Running pytest inside $(TEST_SVC) (the real app env)..."
	@docker exec -w /app $(TEST_SVC) sh -c '\
		python -m pytest --version >/dev/null 2>&1 || pip install -q -r src/tests/requirements-test.txt; \
		python -m pytest src/tests -o asyncio_mode=auto $(PYTEST_ARGS)'

# Banco POS API regression suite -- BLACK-BOX HTTP against the running server.
# Runs from the host .venv (no fastapi needed). ENV=local (default) or ENV=staging.
#   make test-pos                # local  (helix.local)
#   make test-pos ENV=staging    # staging (staging-banco.lapiazza.app)
# See docs/testing/POS-TESTING-SOP.md.
ENV ?= local
.PHONY: test-pos
test-pos:
	@echo "🧪 POS API regression suite (ENV=$(ENV))..."
	@. .venv/bin/activate && ENV=$(ENV) python -m pytest tests/pos -v $(PYTEST_ARGS)

# ===================================================================
# UTILITIES
# ===================================================================

status:
	@REFRESH_INTERVAL=$(or $(REFRESH),60) ./scripts/modules/helix-status-v3.0.1.sh

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
# LEO WATCH - Watch the Lion Work (Real-time Git Monitor)
# "Addicted to Love" - Robert Palmer
# ===================================================================

.PHONY: leo watch-leo

leo:
	@echo ""
	@echo "🦁 LEO IS WATCHING... (Ctrl+C to stop)"
	@echo "═══════════════════════════════════════════════════════"
	@while true; do \
		clear; \
		echo ""; \
		echo "🦁 LEO THE LION — $(shell date '+%H:%M:%S')"; \
		echo "═══════════════════════════════════════════════════════"; \
		echo ""; \
		echo "📍 BRANCH: $$(git branch --show-current)"; \
		echo ""; \
		echo "📊 STATUS:"; \
		git status --short || echo "  (clean)"; \
		echo ""; \
		echo "📝 LAST 5 COMMITS:"; \
		git log --oneline -5 --pretty=format:"  %C(yellow)%h%C(reset) %s" 2>/dev/null || echo "  (no commits)"; \
		echo ""; \
		echo ""; \
		echo "📈 TODAY'S STATS:"; \
		echo "  Commits today: $$(git log --oneline --since='midnight' | wc -l | tr -d ' ')"; \
		echo "  Files changed: $$(git diff --stat HEAD~1 2>/dev/null | tail -1 || echo '0')"; \
		echo ""; \
		echo "═══════════════════════════════════════════════════════"; \
		echo "  ❤️  Heartbeat: ALIVE | 🥏 Frisbee: READY"; \
		echo "═══════════════════════════════════════════════════════"; \
		sleep 2; \
	done

watch-leo: leo

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

# ===================================================================
# BANCO SANDBOX -- the empty Day-One demo instance (runs on the Hetzner box)
#   sandbox-banco.lapiazza.app  ::  container helix-platform-sandbox :8097
#   separate DB banco_sandbox   ::  HX_SEED_DEMO=false (empty catalogue)
# ===================================================================
.PHONY: sandbox-up sandbox-down sandbox-reset sandbox-deploy sandbox-logs

SANDBOX_TREE    := /opt/helix-sandbox-tree
SANDBOX_DB      := banco_sandbox
SANDBOX_SEED    := scripts/sandbox_seed_catalog.sql
SANDBOX_COMPOSE := cd hetzner && docker compose -p hetzner \
	-f docker-compose.uat.yml \
	-f docker-compose.helix-staging.yml \
	-f docker-compose.banco-prod.yml \
	-f docker-compose.banco-sandbox.yml

# Bring the sandbox up: ensure the worktree exists (on origin/main), create the
# empty DB if missing, then start the container. Tables are auto-created on boot.
sandbox-up:
	@echo "==> Ensuring sandbox worktree at origin/main..."
	@git fetch origin -q
	@if [ ! -d "$(SANDBOX_TREE)" ]; then git worktree add --force "$(SANDBOX_TREE)" origin/main; \
	 else git -C "$(SANDBOX_TREE)" checkout --force origin/main -q; fi
	@echo "==> Ensuring database $(SANDBOX_DB) exists..."
	@docker exec postgres psql -U helix_user -d helix_db -tc \
	  "SELECT 1 FROM pg_database WHERE datname='$(SANDBOX_DB)'" | grep -q 1 \
	  || docker exec postgres createdb -U helix_user "$(SANDBOX_DB)"
	@echo "==> Starting helix-platform-sandbox..."
	@$(SANDBOX_COMPOSE) up -d helix-platform-sandbox
	@echo "Sandbox up -> https://sandbox-banco.lapiazza.app/pos"

# Stop the sandbox (hands its RAM back to prod when you are not filming).
sandbox-down:
	@$(SANDBOX_COMPOSE) stop helix-platform-sandbox
	@echo "Sandbox stopped. 'make sandbox-up' to bring it back."

# THE TOOL: zero the shop between takes. Sub-second, idempotent, no restart.
# SOURCE-SCOPED: the reset clears the SALES/transactional tables AND deletes only the
# TAM- demo catalog (sandbox_reset.sql); this step then RE-SEEDS the TAM- products so
# the demo catalog is crisp every night. Manually-created products (LZ-..., future
# MOS-/FTW-) are NEVER touched by the reset -- they persist until a human deletes them,
# so a product a user makes on the fly survives the night. Because the TAM- rows were
# just deleted, the seed re-inserts with no collision; on a brand-new empty DB it simply
# bootstraps. The seed is OPTIONAL (a no-op if absent). Regenerate it with
# scripts/ops/gen_sandbox_seed.py after the demo catalog changes.
sandbox-reset:
	@docker exec -i postgres psql -U helix_user -d $(SANDBOX_DB) -v ON_ERROR_STOP=1 < scripts/sandbox_reset.sql
	@if [ -f "$(SANDBOX_SEED)" ]; then \
		docker exec -i postgres psql -U helix_user -d $(SANDBOX_DB) -v ON_ERROR_STOP=1 < $(SANDBOX_SEED) >/dev/null \
		&& echo "TAM- demo catalog re-seeded ($$(grep -c '^INSERT INTO public.products' $(SANDBOX_SEED)) products)."; \
	fi
	@echo "Sandbox zeroed -- sales/drawers cleared, TAM- catalog refreshed, manual products preserved. Fresh take ready."

# Pull the latest origin/main into the sandbox worktree and restart (code refresh).
sandbox-deploy:
	@git fetch origin -q
	@git -C "$(SANDBOX_TREE)" checkout --force origin/main -q
	@docker restart helix-platform-sandbox
	@echo "Sandbox redeployed at: $$(git -C $(SANDBOX_TREE) rev-parse --short HEAD)"

sandbox-logs:
	@docker logs -f --tail 80 helix-platform-sandbox

# ===================================================================
# END-TO-END WEB-CONSOLE SUITE -- the "the works" gate
# ===================================================================
# Order-to-Cash (O2C): drives a real browser through the full sell-side cycle
#   SIGN-IN -> BROWSE -> FILTER -> FIND -> IDENTIFY -> CART -> CHECKOUT -> PAYMENT -> RECEIPT
# Happy-path verification (not a fuzz/bug-hunt). Self-cleaning: refunds its test
# sale + deactivates its throwaway product, so a nightly/CI run leaves no residue.
# Parameterized -- defaults to sandbox; override E2E_BASE_URL/E2E_USER/... for any env.
# Exit 1 if any journey RED, so it gates a pipeline. Screenshots -> $(E2E_OUT).
#   make e2e                     # against sandbox (default)
#   make e2e E2E_OUT=/tmp/shots  # custom screenshot dir
# A future Procure-to-Pay (P2P / buy-side) sibling plugs in as `make e2e-p2p`.
.PHONY: e2e
E2E_OUT ?= /tmp/banco-e2e
e2e:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_sandbox.js

# MOAT end-to-end — the two Swiss fiscal differentiators, asserted EXACT against a live env:
#   e2e-moat       both: ☕ Two-Price Coffee (per-line VAT) + 🌙 Close-the-Day (Z-report reconcile)
#   e2e-vat        only the Two-Price Coffee VAT journey
#   e2e-closeout   only the Close-the-Day drawer/Z-report journey
# Same harness shape as `make e2e` (parameterized, self-cleaning, exit 1 on RED, screenshots).
.PHONY: e2e-moat e2e-vat e2e-closeout
e2e-moat:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_moat_sandbox.js
e2e-vat:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MOAT_ONLY=vat E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_moat_sandbox.js
e2e-closeout:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MOAT_ONLY=close E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_moat_sandbox.js

# MONEY-PATH end-to-end — the four flows a real cashier hits, asserted against a live env:
#   e2e-money     all four: 💸 Refund · 🔞 Age-gate · 🧾 Mixed-VAT · ⚖️ Variance
#   e2e-refund    only the refund-reverses-money+VAT journey
#   e2e-age       only the 18+ age-gate-fires-at-the-till journey
#   e2e-mixedvat  only the manual mixed-VAT cart + receipt A/B split journey
#   e2e-variance  only the wrong-drawer-count is detected+flagged journey
# Same harness shape as `make e2e` (parameterized, self-cleaning, exit 1 on RED, screenshots).
.PHONY: e2e-money e2e-refund e2e-age e2e-mixedvat e2e-variance
e2e-money:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_money_sandbox.js
e2e-refund:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MONEY_ONLY=refund E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_money_sandbox.js
e2e-age:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MONEY_ONLY=age E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_money_sandbox.js
e2e-mixedvat:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MONEY_ONLY=mixedvat E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_money_sandbox.js
e2e-variance:
	@command -v node >/dev/null || { echo "node is required for the e2e suite"; exit 2; }
	@MONEY_ONLY=variance E2E_OUT=$(E2E_OUT) node scripts/testing/e2e_money_sandbox.js

# The full standard end-to-end run: the O2C "the works" gate + both MOAT differentiators
# + the four money paths a cashier hits.
.PHONY: e2e-all
e2e-all: e2e e2e-moat e2e-money

.PHONY: tailwind
tailwind:
	npx tailwindcss@3.4.17 -c build/tailwind/tailwind.config.js -i build/tailwind/input.css -o src/static/pos/tailwind.css --minify
	@echo "Built src/static/pos/tailwind.css — bump ?v= in pos/base.html + sw.js CACHE_NAME"
