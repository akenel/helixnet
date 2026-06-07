#!/usr/bin/env bash
# ============================================================
# rotate-db-password-align.sh
# ============================================================
# Use case: an app's env file has password X, but Postgres has password Y
# (the situation we hit on 2026-05-12 -- two ALTER USER calls created a
# drift between env and Postgres). This script realigns them safely.
#
# Inputs (interactive, hidden):
#   - Paste the password that's CURRENTLY in your KeePass entry
#     (the value that's also in the env file)
#
# What it does:
#   1. Extract the password from the env file (no echo)
#   2. Compare your pasted value to the env value (silent strcmp)
#   3. If match -> we know KeePass + env + your hand are aligned
#   4. Test asyncpg connection via the docker network (the REAL path)
#   5. ALTER USER ... WITH PASSWORD to make Postgres match
#   6. Restart the app container
#   7. HTTP health check
#
# If any step fails, ABORTS without touching subsequent state.
#
# Usage (run on Hetzner server):
#   bash /opt/helixnet/scripts/rotate-db-password-align.sh
# ============================================================

set -uo pipefail

# Defaults -- override via flags or env vars
ENV_FILE="${ENV_FILE:-/opt/helixnet/hetzner/borrowhood.env}"
DB_NAME="${DB_NAME:-borrowhood}"
DB_USER="${DB_USER:-lapiazza_app}"
PG_CONTAINER="${PG_CONTAINER:-postgres}"
APP_CONTAINER="${APP_CONTAINER:-borrowhood}"
DOCKER_NETWORK="${DOCKER_NETWORK:-hetzner_helixnet}"
APP_URL="${APP_URL:-https://lapiazza.app/}"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/helixnet}"
COMPOSE_FILES="${COMPOSE_FILES:--f hetzner/docker-compose.uat.yml --env-file hetzner/uat.env}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

abort() {
    printf "${RED}✗ ABORT:${NC} %s\n" "$1" >&2
    exit 1
}

step() { printf "${BLUE}▸${NC} %s\n" "$1"; }
ok()   { printf "${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$1"; }

printf "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}\n"
printf "${BLUE}║      Postgres Password Realignment Tool                 ║${NC}\n"
printf "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}\n"
printf "  Env file:        %s\n" "$ENV_FILE"
printf "  DB name:         %s\n" "$DB_NAME"
printf "  DB user:         %s\n" "$DB_USER"
printf "  App container:   %s\n" "$APP_CONTAINER"
printf "  Expected URL OK: %s\n" "$APP_URL"
printf "\n"

# ── 1. Verify env file exists ────────────────────────────────
step "Step 1: Verify env file exists"
[ -f "$ENV_FILE" ] || abort "env file not found: $ENV_FILE"
ok "found"

# ── 2. Extract password from env file ────────────────────────
step "Step 2: Extract password from env file (silent)"
ENV_URL=$(grep '^BH_DATABASE_URL=' "$ENV_FILE" | sed -E 's|^BH_DATABASE_URL=||')
[ -n "$ENV_URL" ] || abort "BH_DATABASE_URL not found in $ENV_FILE"
ENV_USER=$(echo "$ENV_URL" | sed -E 's|^postgresql\+asyncpg://([^:]+):.*|\1|')
ENV_PW=$(echo "$ENV_URL"   | sed -E 's|^postgresql\+asyncpg://[^:]+:([^@]+)@.*|\1|')

if [ "$ENV_USER" != "$DB_USER" ]; then
    abort "env user is '$ENV_USER' but expected '$DB_USER' -- nano edit incomplete?"
fi
ok "env URL parsed: user=$DB_USER, password=${#ENV_PW} chars"

# ── 3. Prompt for password (hidden) ──────────────────────────
step "Step 3: Paste the password from your KeePass entry (hidden input)"
printf "  > "
read -rs PASTED_PW
printf "\n"
if [ -z "$PASTED_PW" ]; then
    abort "no input -- exiting without changes"
fi
printf "  Received %d chars\n" "${#PASTED_PW}"

# ── 4. Verify env password matches what you pasted ───────────
step "Step 4: Verify your paste matches the env file (silent strcmp)"
if [ "$PASTED_PW" = "$ENV_PW" ]; then
    ok "match -- KeePass, env, and your clipboard are aligned"
else
    abort "MISMATCH -- the password in env (${#ENV_PW} chars) does not match what you just pasted (${#PASTED_PW} chars). Fix one of them before proceeding."
fi

# ── 5. Test auth via docker network BEFORE touching Postgres ─
step "Step 5: Test auth via docker network (the REAL path the app uses)"
printf "  Building one-shot python container to test asyncpg connect...\n"
# Note: this tests with the CURRENT Postgres password, which probably still
# doesn't match. That's expected and OK -- it confirms what we already know.
# If this passes here, no ALTER USER needed.
PRE_TEST=$(docker run --rm --network "$DOCKER_NETWORK" --env-file "$ENV_FILE" python:3.12-slim sh -c '
    pip install -q asyncpg 2>&1 >/dev/null
    python -c "
import asyncio, asyncpg, os, sys
async def t():
    url = os.environ[\"BH_DATABASE_URL\"].replace(\"postgresql+asyncpg\", \"postgresql\")
    try:
        conn = await asyncpg.connect(url, timeout=5)
        await conn.close()
        print(\"OK\")
    except asyncpg.InvalidPasswordError:
        print(\"AUTH_FAIL\")
    except Exception as e:
        print(f\"OTHER: {type(e).__name__}\")
asyncio.run(t())
"' 2>&1 | tail -1)

if [ "$PRE_TEST" == "OK" ]; then
    warn "auth already passes -- no Postgres ALTER needed. Just need to restart container if it's running on the old creds."
    SKIP_ALTER=1
elif [ "$PRE_TEST" == "AUTH_FAIL" ]; then
    ok "AUTH_FAIL as expected -- Postgres needs ALTER USER to match env"
    SKIP_ALTER=0
else
    abort "unexpected pre-test result: '$PRE_TEST' (network issue? container down?)"
fi

# ── 6. ALTER USER (only if needed) ───────────────────────────
if [ "${SKIP_ALTER:-0}" = "0" ]; then
    step "Step 6: ALTER USER $DB_USER WITH PASSWORD '<from env>'"
    # Use psql's special parameter binding to safely pass the password.
    # Variables via -v with quote_literal-style escaping aren't perfect for
    # raw text; use here-doc with $PG_PW as the literal in a quoted string.
    # Since our passwords are hex (no quotes/backslashes), simple is fine.
    if echo "ALTER USER $DB_USER WITH PASSWORD '$PASTED_PW';" | \
        docker exec -i "$PG_CONTAINER" psql -U helix_user -d postgres > /tmp/.alter-out 2>&1; then
        if grep -q "ALTER ROLE" /tmp/.alter-out; then
            ok "Postgres password updated"
        else
            cat /tmp/.alter-out
            abort "ALTER USER didn't return 'ALTER ROLE' -- something weird, check above"
        fi
    else
        cat /tmp/.alter-out
        abort "ALTER USER failed"
    fi
    rm -f /tmp/.alter-out

    # ── 7. Verify ALTER worked (re-test via docker network) ─
    step "Step 7: Re-test auth via docker network (should pass now)"
    POST_TEST=$(docker run --rm --network "$DOCKER_NETWORK" --env-file "$ENV_FILE" python:3.12-slim sh -c '
        pip install -q asyncpg 2>&1 >/dev/null
        python -c "
import asyncio, asyncpg, os
async def t():
    url = os.environ[\"BH_DATABASE_URL\"].replace(\"postgresql+asyncpg\", \"postgresql\")
    conn = await asyncpg.connect(url, timeout=5)
    await conn.close()
    print(\"OK\")
asyncio.run(t())
"' 2>&1 | tail -1)
    [ "$POST_TEST" = "OK" ] || abort "ALTER USER set, but asyncpg still can't auth: $POST_TEST"
    ok "asyncpg connects -- Postgres and env are aligned"
fi

# ── 8. Restart the app container ─────────────────────────────
step "Step 8: Restart $APP_CONTAINER container"
cd "$COMPOSE_DIR"
docker compose $COMPOSE_FILES up -d --force-recreate "$APP_CONTAINER" 2>&1 | tail -3

printf "  Wait 40s for startup + migrations...\n"
sleep 40

STATUS=$(docker ps --filter "name=^${APP_CONTAINER}$" --format '{{.Status}}')
printf "  Container status: %s\n" "$STATUS"

# ── 9. HTTP health check ─────────────────────────────────────
step "Step 9: HTTP health check"
CODE=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 "$APP_URL")
if [ "$CODE" = "200" ]; then
    ok "$APP_URL -> 200"
else
    abort "$APP_URL -> $CODE (check 'docker logs $APP_CONTAINER')"
fi

printf "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}\n"
printf "${GREEN}║      ✓ REALIGNMENT COMPLETE -- prod healthy             ║${NC}\n"
printf "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}\n"
