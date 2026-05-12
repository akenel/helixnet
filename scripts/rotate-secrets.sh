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

# ── helper: Postgres password is special (embedded in DATABASE_URL) ──
rotate_db_password() {
    printf "${BLUE}──── BH_DATABASE_URL (Postgres password) ────${NC}\n"
    printf "  Special: password is embedded inside the connection URL.\n"
    printf "  Format: postgresql+asyncpg://<user>:<password>@postgres:5432/<db>\n"
    printf "  paste NEW password only -- script rebuilds the URL: "
    read -rs new_pass
    printf "\n"

    if [ -z "$new_pass" ]; then
        printf "  ${YELLOW}skipped${NC}\n\n"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return
    fi

    # Extract the existing user + db from the current URL (preserve them)
    local current_url
    current_url=$(grep "^BH_DATABASE_URL=" "$ENV_FILE" | cut -d= -f2-)
    # Pattern: postgresql+asyncpg://USER:OLD_PASS@HOST:PORT/DB
    local user host_port_db
    user=$(echo "$current_url" | sed -E 's|^postgresql\+asyncpg://([^:]+):.*|\1|')
    host_port_db=$(echo "$current_url" | sed -E 's|^postgresql\+asyncpg://[^:]+:[^@]+@(.*)|\1|')

    local new_url="postgresql+asyncpg://${user}:${new_pass}@${host_port_db}"
    update_key_value "BH_DATABASE_URL" "$new_url"
    printf "  ${GREEN}updated${NC} BH_DATABASE_URL (password %d chars)\n" "${#new_pass}"
    printf "  ${YELLOW}NEXT STEP (manual):${NC} apply the same password to Postgres itself:\n"
    printf "      docker exec -it postgres psql -U helix_user -d postgres\n"
    printf "      ALTER USER %s WITH PASSWORD '<paste new password>';\n" "$user"
    printf "      \\\\q\n\n"
    UPDATED_COUNT=$((UPDATED_COUNT + 1))
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
        printf "    ${RED}https://lapiazza.app/ -> %s${NC} -- check logs: docker logs borrowhood\n" "$code"
        printf "    ${YELLOW}Rollback:${NC} cp $BACKUP_FILE $ENV_FILE && docker compose ... up -d --force-recreate borrowhood\n"
        exit 1
    fi
    code_oidc=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 10 https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration)
    if [ "$code_oidc" == "200" ]; then
        printf "    ${GREEN}OIDC discovery -> 200 OK${NC}\n"
    else
        printf "    ${RED}OIDC discovery -> %s${NC} -- KC client secret may be wrong\n" "$code_oidc"
    fi
fi

printf "\n  ${BLUE}Done.${NC}\n"
printf "  When you've verified everything works, shred the temp keys file:\n"
printf "      shred -u /opt/helixnet/hetzner/LP-TMP_KEYS.TXT\n"
printf "  (shred overwrites the bytes before unlinking -- safer than rm)\n\n"
