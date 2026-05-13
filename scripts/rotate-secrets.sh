#!/usr/bin/env bash
# ============================================================
# rotate-secrets.sh -- Interactive secret rotation for La Piazza
# ============================================================
# Walks through each prod secret. For each:
#   - Shows the key name + description + current value length
#   - Prompts for the NEW value with hidden input (read -s)
#   - Empty input = SKIP (keep existing value)
#   - Otherwise: replaces the value in borrowhood.env in place
#
# Values are never echoed to the screen, never logged.
# Source: paste from KeePass.
# After: container restart + health check.
#
# Run from the Hetzner server:
#   bash /opt/helixnet/scripts/rotate-secrets.sh
# ============================================================

set -uo pipefail

ENV_FILE=/opt/helixnet/hetzner/borrowhood.env
BACKUP_DIR=/opt/backup-2026-05-10
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/borrowhood.env.before-rotation-$(date +%Y%m%d-%H%M%S)"

# ── DB rotation state (used by auto-rollback) ─────────────────
DB_ROTATED=0
DB_OLD_USER=""
DB_OLD_PASS=""
DOCKER_NETWORK="${DOCKER_NETWORK:-hetzner_helixnet}"
PG_CONTAINER="${PG_CONTAINER:-postgres}"

# ── output helpers ───────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -f "$ENV_FILE" ]; then
    printf "${RED}ERROR:${NC} $ENV_FILE not found\n" >&2
    exit 1
fi

# Backup BEFORE any change
cp "$ENV_FILE" "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"

printf "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}\n"
printf "${BLUE}║   La Piazza Production -- Interactive Secret Rotation    ║${NC}\n"
printf "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}\n"
printf "  Env file:   %s\n" "$ENV_FILE"
printf "  Backup at:  %s\n" "$BACKUP_FILE"
printf "  Started:    %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf "\n  ${YELLOW}For each key: paste the new value from KeePass and press Enter.${NC}\n"
printf "  ${YELLOW}Press Enter on an empty line to SKIP that key.${NC}\n"
printf "  ${YELLOW}Values are hidden as you paste -- nothing is echoed.${NC}\n"
printf "\n"

UPDATED_COUNT=0
SKIPPED_COUNT=0

# ── helper: update one key in place using awk (handles special chars) ──
update_key_value() {
    local key="$1"
    local val="$2"
    # Use awk with -v to safely pass the new value; print line as-is otherwise.
    # The key=val format is preserved exactly.
    awk -v k="$key" -v v="$val" '
        $0 ~ "^"k"=" { printf "%s=%s\n", k, v; updated=1; next }
        { print }
        END { if (!updated) print k"="v }
    ' "$ENV_FILE" > "${ENV_FILE}.new"
    mv "${ENV_FILE}.new" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
}

# ── helper: prompt for a single secret ───────────────────────
rotate() {
    local key="$1"
    local desc="$2"
    local current_line
    current_line=$(grep "^${key}=" "$ENV_FILE" 2>/dev/null || echo "${key}=<absent>")
    local current_len=$(( ${#current_line} - ${#key} - 1 ))

    printf "${BLUE}──── %s ────${NC}\n" "$key"
    printf "  ${desc}\n"
    printf "  current length: %s chars\n" "$current_len"
    printf "  paste new value (Enter = skip): "
    # -s = silent (no echo), -r = raw (don't interpret backslashes)
    read -rs new_val
    printf "\n"

    if [ -z "$new_val" ]; then
        printf "  ${YELLOW}skipped${NC}\n\n"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return
    fi

    update_key_value "$key" "$new_val"
    printf "  ${GREEN}updated${NC} (%d chars)\n\n" "${#new_val}"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
}

# ── helper: asyncpg test via docker network (REAL auth path) ──
# Returns "OK" / "AUTH_FAIL" / "OTHER:<reason>"
test_asyncpg() {
    local url="$1"
    docker run --rm --network "$DOCKER_NETWORK" \
        -e TEST_URL="$url" \
        python:3.12-slim sh -c '
            pip install -q asyncpg 2>&1 >/dev/null
            python -c "
import asyncio, asyncpg, os
async def t():
    url = os.environ[\"TEST_URL\"].replace(\"postgresql+asyncpg\", \"postgresql\")
    try:
        conn = await asyncpg.connect(url, timeout=5)
        await conn.close()
        print(\"OK\")
    except asyncpg.InvalidPasswordError:
        print(\"AUTH_FAIL\")
    except Exception as e:
        print(f\"OTHER:{type(e).__name__}\")
asyncio.run(t())
"' 2>/dev/null | tail -1
}

# ── helper: ALTER USER in Postgres (returns 0 on success) ──
psql_alter_user() {
    local pg_user="$1"
    local pg_pass="$2"
    # Hex passwords are quote-safe; warn if not pure hex
    if ! [[ "$pg_pass" =~ ^[a-fA-F0-9]+$ ]]; then
        printf "  ${YELLOW}WARN:${NC} password is not pure hex; psql quoting may fail.\n" >&2
    fi
    echo "ALTER USER $pg_user WITH PASSWORD '$pg_pass';" | \
        docker exec -i "$PG_CONTAINER" psql -U helix_user -d postgres 2>&1 | \
        grep -q "ALTER ROLE"
}

# ── helper: Postgres password rotation (HARDENED) ──
# Pre-test → ALTER USER → update env → post-test → rollback on failure.
rotate_db_password() {
    printf "${BLUE}──── BH_DATABASE_URL (Postgres password) ────${NC}\n"
    printf "  Special: password is in URL + must also ALTER USER in Postgres.\n"
    printf "  ${YELLOW}TIP: use hex-only password (openssl rand -hex 32) for safe quoting.${NC}\n"

    # Extract current user + host_port_db + OLD password from env
    local current_url
    current_url=$(grep "^BH_DATABASE_URL=" "$ENV_FILE" | cut -d= -f2-)
    local user host_port_db old_pass
    user=$(echo "$current_url" | sed -E 's|^postgresql\+asyncpg://([^:]+):.*|\1|')
    host_port_db=$(echo "$current_url" | sed -E 's|^postgresql\+asyncpg://[^:]+:[^@]+@(.*)|\1|')
    old_pass=$(echo "$current_url" | sed -E 's|^postgresql\+asyncpg://[^:]+:([^@]+)@.*|\1|')

    printf "  current user:     %s\n" "$user"
    printf "  current pw chars: %d\n" "${#old_pass}"
    printf "  paste NEW password (Enter = skip): "
    read -rs new_pass
    printf "\n"

    if [ -z "$new_pass" ]; then
        printf "  ${YELLOW}skipped${NC}\n\n"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return
    fi

    # Step 1: PRE-TEST -- verify current env actually authenticates (sanity)
    printf "  ${BLUE}pre-test:${NC} verifying current env+Postgres are aligned..."
    local pre
    pre=$(test_asyncpg "$current_url")
    if [ "$pre" != "OK" ]; then
        printf " ${RED}FAIL ($pre)${NC}\n"
        printf "  ${RED}ABORT:${NC} current env doesn't authenticate. System is already broken.\n"
        printf "  Fix the existing state first; don't rotate on top of broken auth.\n\n"
        return
    fi
    printf " ${GREEN}OK${NC}\n"

    # Step 2: ALTER USER in Postgres
    printf "  ${BLUE}altering:${NC} ALTER USER $user WITH PASSWORD ..."
    if ! psql_alter_user "$user" "$new_pass"; then
        printf " ${RED}FAIL${NC}\n"
        printf "  ${RED}ABORT:${NC} ALTER USER failed. Env unchanged. Postgres unchanged.\n\n"
        return
    fi
    printf " ${GREEN}done${NC}\n"

    # Step 3: Update env file
    local new_url="postgresql+asyncpg://${user}:${new_pass}@${host_port_db}"
    update_key_value "BH_DATABASE_URL" "$new_url"

    # Step 4: POST-TEST -- verify new password works
    printf "  ${BLUE}post-test:${NC} asyncpg connect with new password..."
    local post
    post=$(test_asyncpg "$new_url")
    if [ "$post" != "OK" ]; then
        printf " ${RED}FAIL ($post)${NC}\n"
        printf "  ${RED}AUTO-ROLLBACK:${NC} restoring env + ALTER USER back to old password\n"
        cp "$BACKUP_FILE" "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        psql_alter_user "$user" "$old_pass" && \
            printf "    ${GREEN}rolled back${NC}\n\n" || \
            printf "    ${RED}ROLLBACK FAILED${NC} -- manual recovery needed\n\n"
        return
    fi
    printf " ${GREEN}OK${NC}\n"

    # Success: save state for end-of-script auto-rollback on health-check fail
    DB_ROTATED=1
    DB_OLD_USER="$user"
    DB_OLD_PASS="$old_pass"

    printf "  ${GREEN}updated${NC} env + Postgres aligned (%d chars)\n\n" "${#new_pass}"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
}

# ── helper: end-of-script auto-rollback (called on health-check fail) ──
auto_rollback() {
    printf "\n  ${RED}AUTO-ROLLBACK STARTING${NC}\n"
    cp "$BACKUP_FILE" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    printf "    env restored from %s\n" "$BACKUP_FILE"

    if [ "$DB_ROTATED" = "1" ]; then
        printf "    ALTER USER $DB_OLD_USER back to old password..."
        psql_alter_user "$DB_OLD_USER" "$DB_OLD_PASS" && \
            printf " ${GREEN}done${NC}\n" || \
            printf " ${RED}FAILED${NC} -- manual recovery needed\n"
    fi

    printf "    restarting container with restored env...\n"
    cd /opt/helixnet
    docker compose -f hetzner/docker-compose.uat.yml \
        --env-file hetzner/uat.env \
        up -d --force-recreate borrowhood 2>&1 | tail -3
    sleep 30

    local code
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 https://lapiazza.app/)
    if [ "$code" = "200" ]; then
        printf "    ${GREEN}rollback complete -- lapiazza.app -> 200${NC}\n"
    else
        printf "    ${RED}rollback INCOMPLETE -- lapiazza.app -> $code${NC}\n"
        printf "    Manual: docker logs borrowhood | tail -50\n"
    fi
}

# ── The 9 La Piazza prod secrets (in severity order) ────────────────
rotate           "BH_SECRET_KEY"           "Flask session signing key. Side effect: kicks out all logged-in users."
rotate_db_password
rotate           "BH_KC_CLIENT_SECRET"     "Keycloak borrowhood-web OIDC client secret (from KC admin UI)."
rotate           "BH_TELEGRAM_BOT_TOKEN"   "Telegram bot API token (from @BotFather, format <id>:<hash>)."
rotate           "BH_RESEND_API_KEY"       "Resend email API key (re_xxx...)."
rotate           "BH_OLLAMA_KEY"           "Ollama Cloud API key (gemma3:12b model)."
rotate           "BH_PAYPAL_CLIENT_SECRET" "PayPal sandbox client secret (developer.paypal.com)."
rotate           "KC_GITHUB_CLIENT_SECRET" "Keycloak GitHub IDP secret (github.com/settings/developers)."
rotate           "KC_GOOGLE_CLIENT_SECRET" "Keycloak Google IDP secret (console.cloud.google.com)."

# ── Summary ──────────────────────────────────────────────────
printf "${BLUE}══════════════════════════════════════════════════════════${NC}\n"
printf "  ${GREEN}Updated:${NC} %d secrets\n" "$UPDATED_COUNT"
printf "  ${YELLOW}Skipped:${NC} %d secrets\n" "$SKIPPED_COUNT"
printf "  Backup:   %s\n" "$BACKUP_FILE"
printf "${BLUE}══════════════════════════════════════════════════════════${NC}\n\n"

# ── Restart prompt ───────────────────────────────────────────
if [ "$UPDATED_COUNT" -eq 0 ]; then
    printf "  No changes made. Nothing to restart.\n"
    exit 0
fi

printf "  Restart borrowhood container now to load new secrets? [y/N] "
read -r restart_yn

if [[ "$restart_yn" =~ ^[Yy]$ ]]; then
    printf "\n  Restarting...\n"
    cd /opt/helixnet
    docker compose -f hetzner/docker-compose.uat.yml \
        --env-file hetzner/uat.env \
        up -d --force-recreate borrowhood 2>&1 | tail -3
    sleep 30
    printf "\n  ${BLUE}Health check:${NC}\n"
    code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 https://lapiazza.app/)
    if [ "$code" == "200" ]; then
        printf "    ${GREEN}https://lapiazza.app/ -> 200 OK${NC}\n"
    else
        printf "    ${RED}https://lapiazza.app/ -> %s${NC}\n" "$code"
        printf "    Logs (last 30 lines):\n"
        docker logs borrowhood 2>&1 | tail -30 | sed 's/^/      /'
        auto_rollback
        exit 1
    fi
    code_oidc=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration)
    if [ "$code_oidc" == "200" ]; then
        printf "    ${GREEN}OIDC discovery -> 200 OK${NC}\n"
    else
        printf "    ${YELLOW}OIDC discovery -> %s${NC} -- KC client secret may be wrong (not auto-rolled, recoverable)\n" "$code_oidc"
    fi
fi

printf "\n  ${BLUE}Done.${NC}\n"
printf "  When you've verified everything works, shred the temp keys file:\n"
printf "      shred -u /opt/helixnet/hetzner/LP-TMP_KEYS.TXT\n"
printf "  (shred overwrites the bytes before unlinking -- safer than rm)\n\n"
