#!/usr/bin/env bash
# ============================================================
# preflight.sh -- 25-point pre-deploy inspection
# ============================================================
# Run BEFORE any deploy gate or CI/CD workflow trusts the box.
# Inspired by the camper-van seal-inspection lesson: if one seal
# fails, check them all. Catches the gotchas that took down prod
# on May 10 and May 11.
#
# Run from the Hetzner server:
#   bash /opt/helixnet/scripts/preflight.sh
#
# Or via SSH from any machine with the key:
#   ssh root@46.62.138.218 "bash /opt/helixnet/scripts/preflight.sh"
#
# Exit codes:
#   0   = all green
#   1   = one or more FAIL (cannot deploy)
#   2   = WARN only (deploy allowed but flag for follow-up)
#
# Optional: set NOTIFY_TELEGRAM=1 to ping the ops bot on failure.
# ============================================================

set -u

HELIX_ROOT="${HELIX_ROOT:-/opt/helixnet}"
BORROWHOOD_ROOT="${BORROWHOOD_ROOT:-/opt/helixnet/BorrowHood}"
HOSTNAME_PROD="${HOSTNAME_PROD:-lapiazza.app}"
HOSTNAME_STAGING="${HOSTNAME_STAGING:-staging.lapiazza.app}"
PUBLIC_IP="${PUBLIC_IP:-46.62.138.218}"

# Color codes for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
FAILURES=()
WARNINGS=()

# ── output helpers ───────────────────────────────────────────
pass() {
    printf "${GREEN}✓${NC}  %-6s %s\n" "$1" "$2"
    PASS_COUNT=$((PASS_COUNT + 1))
}
fail() {
    printf "${RED}✗${NC}  %-6s %s\n" "$1" "$2"
    FAILURES+=("$1: $2")
    FAIL_COUNT=$((FAIL_COUNT + 1))
}
warn() {
    printf "${YELLOW}!${NC}  %-6s %s\n" "$1" "$2"
    WARNINGS+=("$1: $2")
    WARN_COUNT=$((WARN_COUNT + 1))
}
info() {
    printf "${BLUE}i${NC}  %s\n" "$1"
}
section() {
    printf "\n${BLUE}── %s ──${NC}\n" "$1"
}

# ── check helpers ────────────────────────────────────────────
docker_running() {
    docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^$1$"
}

docker_healthy() {
    local status
    status=$(docker ps --filter "name=$1" --format '{{.Status}}' 2>/dev/null)
    [[ "$status" == *"healthy"* ]]
}

# ============================================================
printf "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}\n"
printf "${BLUE}║      La Piazza / HelixNet -- 25-Point Preflight         ║${NC}\n"
printf "${BLUE}║      $(date -u +%Y-%m-%dT%H:%M:%SZ)                                ║${NC}\n"
printf "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}\n"

# ── SECTION 1: Filesystem + Git ──────────────────────────────
section "Filesystem + Git"

# 0.1
if [ -d "$HELIX_ROOT/.git" ]; then
    pass "0.1" "helixnet repo at $HELIX_ROOT"
else
    fail "0.1" "$HELIX_ROOT is not a git checkout"
fi

# 0.2
if [ -d "$BORROWHOOD_ROOT/.git" ]; then
    pass "0.2" "BorrowHood repo at $BORROWHOOD_ROOT"
else
    fail "0.2" "$BORROWHOOD_ROOT is not a git checkout"
fi

# 0.3
if git -C "$BORROWHOOD_ROOT" config user.email > /dev/null 2>&1; then
    pass "0.3" "git identity set: $(git -C "$BORROWHOOD_ROOT" config user.email)"
else
    fail "0.3" "git user.email not configured in BorrowHood (deploys via SSH will fail to commit)"
fi

# 0.4
if [ -f "$HELIX_ROOT/hetzner/docker-compose.uat.yml" ] && [ -f "$HELIX_ROOT/hetzner/docker-compose.staging.yml" ]; then
    pass "0.4" "compose files present (uat + staging)"
else
    fail "0.4" "missing one of hetzner/docker-compose.{uat,staging}.yml"
fi

# 0.5
if [ -f "$HELIX_ROOT/hetzner/borrowhood.env" ] && [ -f "$HELIX_ROOT/hetzner/.env.staging" ] && [ -f "$HELIX_ROOT/hetzner/uat.env" ]; then
    pass "0.5" "env files present (borrowhood.env, .env.staging, uat.env)"
else
    fail "0.5" "missing one of hetzner/{borrowhood.env, .env.staging, uat.env}"
fi

# 0.6 -- env files MUST be gitignored
ignored=true
for f in borrowhood.env .env.staging uat.env; do
    if ! git -C "$HELIX_ROOT" check-ignore -q "hetzner/$f" 2>/dev/null; then
        ignored=false
        break
    fi
done
if $ignored; then
    pass "0.6" "all env files gitignored (no future secret leaks)"
else
    fail "0.6" "one or more env files NOT gitignored -- secrets could be committed"
fi

# 0.7 -- HELIX_PUBLIC_HOST in uat.env (the May 10 prod-takedown gotcha)
if grep -q "^HELIX_PUBLIC_HOST=" "$HELIX_ROOT/hetzner/uat.env" 2>/dev/null; then
    pass "0.7" "HELIX_PUBLIC_HOST set in uat.env (gotcha #1 guarded)"
else
    fail "0.7" "HELIX_PUBLIC_HOST MISSING from uat.env -- next keycloak recreate will crash"
fi

# ── SECTION 2: Containers ────────────────────────────────────
section "Container health"

# 0.8 -- core containers running
for c in postgres keycloak caddy borrowhood; do
    if docker_running "$c"; then
        if docker_healthy "$c"; then
            pass "0.8-$c" "$c container healthy"
        else
            status=$(docker ps --filter "name=$c" --format '{{.Status}}')
            warn "0.8-$c" "$c running but status: $status"
        fi
    else
        fail "0.8-$c" "$c container NOT running"
    fi
done

# 0.9 -- staging container can start (optional, may be intentionally stopped)
if docker_running borrowhood_staging; then
    pass "0.9" "borrowhood_staging running"
else
    warn "0.9" "borrowhood_staging not running (acceptable -- staging is ephemeral)"
fi

# 0.10 -- Caddyfile bind mount inode match (the May 11 stale-mount gotcha)
host_md5=$(md5sum "$HELIX_ROOT/hetzner/Caddyfile" 2>/dev/null | cut -d' ' -f1)
container_md5=$(docker exec caddy md5sum /etc/caddy/Caddyfile 2>/dev/null | cut -d' ' -f1)
if [ -n "$host_md5" ] && [ "$host_md5" == "$container_md5" ]; then
    pass "0.10" "Caddyfile bind-mount fresh (host == container) (gotcha #2 guarded)"
else
    fail "0.10" "Caddyfile bind-mount STALE -- host md5=$host_md5 container md5=$container_md5 -- restart caddy"
fi

# 0.11 -- Postgres reachable from outside via docker exec
if docker exec -i postgres pg_isready -U helix_user > /dev/null 2>&1; then
    pass "0.11" "postgres accepting connections"
else
    fail "0.11" "postgres pg_isready FAILED"
fi

# 0.12 -- prod DB exists
if docker exec -i postgres psql -U helix_user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='borrowhood'" | grep -q 1; then
    pass "0.12" "borrowhood (prod) DB present"
else
    fail "0.12" "borrowhood DB MISSING"
fi

# 0.13 -- staging DB exists
if docker exec -i postgres psql -U helix_user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='borrowhood_staging'" | grep -q 1; then
    pass "0.13" "borrowhood_staging DB present"
else
    fail "0.13" "borrowhood_staging DB MISSING"
fi

# 0.14 -- Keycloak realms imported
realm_count=$(docker exec keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user helix_user --password helix_pass > /dev/null 2>&1 && \
    docker exec keycloak /opt/keycloak/bin/kcadm.sh get realms --fields realm 2>/dev/null | grep -cE '"borrowhood' )
realm_count=${realm_count:-0}
if [ "$realm_count" -ge 2 ]; then
    pass "0.14" "Keycloak: borrowhood + borrowhood-staging realms present"
elif [ "$realm_count" -eq 1 ]; then
    warn "0.14" "Keycloak: only 1 borrowhood-style realm present (expected 2)"
else
    fail "0.14" "Keycloak: borrowhood realms missing (kcadm auth ok? both realms imported?)"
fi

# ── SECTION 3: Network + DNS + TLS ───────────────────────────
section "Network + DNS + TLS"

# 0.15 -- DNS for prod
prod_ip=$(dig +short "$HOSTNAME_PROD" @1.1.1.1 2>/dev/null | head -1)
if [ "$prod_ip" == "$PUBLIC_IP" ]; then
    pass "0.15" "DNS: $HOSTNAME_PROD -> $PUBLIC_IP"
else
    fail "0.15" "DNS: $HOSTNAME_PROD -> '$prod_ip' (expected $PUBLIC_IP)"
fi

# 0.16 -- DNS for staging
staging_ip=$(dig +short "$HOSTNAME_STAGING" @1.1.1.1 2>/dev/null | head -1)
if [ "$staging_ip" == "$PUBLIC_IP" ]; then
    pass "0.16" "DNS: $HOSTNAME_STAGING -> $PUBLIC_IP"
else
    fail "0.16" "DNS: $HOSTNAME_STAGING -> '$staging_ip' (expected $PUBLIC_IP)"
fi

# 0.17 -- Let's Encrypt cert for prod present
if docker exec caddy test -d "/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/$HOSTNAME_PROD" 2>/dev/null; then
    pass "0.17" "LE cert: $HOSTNAME_PROD present"
else
    fail "0.17" "LE cert: $HOSTNAME_PROD MISSING -- Caddy auto-issue may have failed"
fi

# 0.18 -- LE cert for staging
if docker exec caddy test -d "/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/$HOSTNAME_STAGING" 2>/dev/null; then
    pass "0.18" "LE cert: $HOSTNAME_STAGING present"
else
    warn "0.18" "LE cert: $HOSTNAME_STAGING MISSING (acceptable if staging not yet hit)"
fi

# ── SECTION 4: Live HTTP smoke ───────────────────────────────
section "Live HTTP smoke"

# 0.19 -- prod root
code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 8 "https://$HOSTNAME_PROD/" 2>/dev/null)
if [ "$code" == "200" ]; then
    pass "0.19" "GET https://$HOSTNAME_PROD/ -> 200"
else
    fail "0.19" "GET https://$HOSTNAME_PROD/ -> $code"
fi

# 0.20 -- prod OIDC discovery
code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 8 "https://$HOSTNAME_PROD/realms/borrowhood/.well-known/openid-configuration")
if [ "$code" == "200" ]; then
    pass "0.20" "OIDC discovery (prod): 200"
else
    fail "0.20" "OIDC discovery (prod): $code -- keycloak may be down"
fi

# 0.21 -- staging realm OIDC discovery
code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 8 "https://$HOSTNAME_STAGING/realms/borrowhood-staging/.well-known/openid-configuration")
if [ "$code" == "200" ]; then
    pass "0.21" "OIDC discovery (staging realm): 200"
else
    warn "0.21" "OIDC discovery (staging): $code (acceptable if staging container not running)"
fi

# 0.22 -- staging realm frontendUrl override (the May 12 cookie-domain gotcha)
# Don't use --fields attributes -- it returns empty in some kcadm versions
front_url=$(docker exec keycloak /opt/keycloak/bin/kcadm.sh get realms/borrowhood-staging 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('attributes', {}).get('frontendUrl', ''))
except Exception:
    print('')
" 2>/dev/null)
if [ "$front_url" == "https://$HOSTNAME_STAGING" ]; then
    pass "0.22" "staging realm frontendUrl=https://$HOSTNAME_STAGING (gotcha #3 guarded)"
else
    fail "0.22" "staging realm frontendUrl='$front_url' (expected https://$HOSTNAME_STAGING) -- cookies will break"
fi

# ── SECTION 5: Operational ───────────────────────────────────
section "Operational"

# 0.23 -- free RAM > 1.5GB
free_mb=$(free -m | awk '/^Mem:/ {print $7}')
if [ "$free_mb" -gt 1500 ]; then
    pass "0.23" "Free RAM: ${free_mb}MB (>1.5GB)"
elif [ "$free_mb" -gt 500 ]; then
    warn "0.23" "Free RAM: ${free_mb}MB (low but workable)"
else
    fail "0.23" "Free RAM: ${free_mb}MB (too low to safely deploy new container)"
fi

# 0.24 -- free disk > 5GB
free_gb=$(df -BG / | awk 'NR==2 {gsub("G","",$4); print $4}')
if [ "$free_gb" -gt 5 ]; then
    pass "0.24" "Free disk: ${free_gb}GB"
elif [ "$free_gb" -gt 2 ]; then
    warn "0.24" "Free disk: ${free_gb}GB (clean up soon)"
else
    fail "0.24" "Free disk: ${free_gb}GB (deploy will fail)"
fi

# 0.25 -- recent prod 500s in logs
# grep -c returns 0 lines but exit 1 when no match; force exit 0 so we get a clean int
err_count=$(docker logs --since 30m borrowhood 2>&1 | grep -c "Internal Server Error\|Traceback" 2>/dev/null || true)
err_count=${err_count:-0}
err_count=$(echo "$err_count" | head -1)  # belt + suspenders
if [ "$err_count" -eq 0 ] 2>/dev/null; then
    pass "0.25" "no 500s/tracebacks in prod logs (last 30 min)"
elif [ "$err_count" -lt 5 ]; then
    warn "0.25" "$err_count 500s/tracebacks in prod logs (last 30 min)"
else
    fail "0.25" "$err_count 500s/tracebacks in prod logs (last 30 min) -- investigate before deploying"
fi

# ── Summary ──────────────────────────────────────────────────
printf "\n${BLUE}╔══════════════════════════════════════════════════════════╗${NC}\n"
printf "${BLUE}║                      SUMMARY                             ║${NC}\n"
printf "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}\n"
printf "  ${GREEN}PASS:${NC} %d\n  ${YELLOW}WARN:${NC} %d\n  ${RED}FAIL:${NC} %d\n\n" "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf "${RED}── FAILURES ──${NC}\n"
    for f in "${FAILURES[@]}"; do printf "  %s\n" "$f"; done
    printf "\n"
fi
if [ "$WARN_COUNT" -gt 0 ]; then
    printf "${YELLOW}── WARNINGS ──${NC}\n"
    for w in "${WARNINGS[@]}"; do printf "  %s\n" "$w"; done
    printf "\n"
fi

# Optional Telegram notification on failure
if [ "${NOTIFY_TELEGRAM:-0}" == "1" ] && [ "$FAIL_COUNT" -gt 0 ]; then
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_AUTHORIZED_USER_ID:-}" ]; then
        msg="[CI/CD] Preflight FAILED on $(hostname): $FAIL_COUNT fails, $WARN_COUNT warns. Top: ${FAILURES[0]}"
        curl -sk -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_AUTHORIZED_USER_ID}" \
            -d "text=${msg}" > /dev/null 2>&1 \
            && printf "${BLUE}i${NC}  Telegram alert sent.\n"
    fi
fi

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf "${RED}OVERALL: FAIL${NC} -- deploy must NOT proceed\n"
    exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
    printf "${YELLOW}OVERALL: WARN${NC} -- deploy allowed, fix the warnings soon\n"
    exit 2
else
    printf "${GREEN}OVERALL: ALL GREEN${NC} -- safe to deploy\n"
    exit 0
fi
