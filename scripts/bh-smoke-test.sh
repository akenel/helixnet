#!/usr/bin/env bash
# ============================================================
# BorrowHood Post-Deploy Smoke Test
# Usage: ./scripts/bh-smoke-test.sh [local|hetzner]
# ============================================================
set -euo pipefail

MODE="${1:-hetzner}"
if [ "$MODE" = "local" ]; then
  BASE="https://localhost"
else
  BASE="https://46.62.138.218"
fi

PASS=0; FAIL=0; TOTAL=0
KC_CLIENT="borrowhood-web"

ok()   { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  \033[32m✓\033[0m $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  \033[31m✗\033[0m $1"; }
section() { echo "\033[1;36m── $1 ──\033[0m"; }

# Banner
echo "\033[1;37m"
echo "╔══════════════════════════════════════════════════╗"
echo "║      BorrowHood Smoke Test                      ║"
echo "║      Target: ${MODE^^} ($BASE)                  ║"
echo "╚══════════════════════════════════════════════════╝"
echo "\033[0m"

# ── 1. Page Checks ──
section "1. HTML Pages"

for path in "/" "/demo-login" "/browse" "/members" "/terms"; do
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$BASE$path" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    ok "GET $path ($CODE)"
  else
    fail "GET $path (expected 200, got $CODE)"
  fi
done

# Login page redirects to Keycloak (302 or 307)
CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/login" 2>/dev/null)
if [ "$CODE" = "302" ] || [ "$CODE" = "307" ]; then
  ok "GET /login (redirect $CODE to Keycloak)"
else
  fail "GET /login (expected 302/307, got $CODE)"
fi

# ── 2. Static Assets ──
section "2. Static Assets"

# Avatar files
AVATAR_OK=0; AVATAR_FAIL=0
for av in angel.jpg sally.svg mike.svg nino.svg pietro.svg george.svg leonardo.svg john.svg sofia.svg anne.svg; do
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/static/images/avatars/$av" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    AVATAR_OK=$((AVATAR_OK+1))
  else
    AVATAR_FAIL=$((AVATAR_FAIL+1))
  fi
done
if [ "$AVATAR_FAIL" -eq 0 ]; then
  ok "Cast avatars: $AVATAR_OK/10 accessible"
else
  fail "Cast avatars: $AVATAR_OK accessible, $AVATAR_FAIL missing"
fi

# ── 3. Keycloak Auth ──
section "3. Keycloak Authentication"

# Test all 14 cast members can get tokens
CAST_USERS="sally mike angel nino maria marco pietro jake rosa george leonardo john sofiaferretti anne"
AUTH_OK=0; AUTH_FAIL=0; AUTH_FAILS=""

for u in $CAST_USERS; do
  RESP=$(curl -sk -X POST "$BASE/realms/borrowhood/protocol/openid-connect/token" \
    -d "client_id=$KC_CLIENT" \
    -d "grant_type=password" \
    -d "username=$u" \
    -d "password=helix_pass" 2>/dev/null)
  if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'access_token' in d else 1)" 2>/dev/null; then
    AUTH_OK=$((AUTH_OK+1))
  else
    AUTH_FAIL=$((AUTH_FAIL+1))
    AUTH_FAILS="$AUTH_FAILS $u"
  fi
done

if [ "$AUTH_FAIL" -eq 0 ]; then
  ok "All 14 cast members authenticate"
else
  fail "Auth failures ($AUTH_FAIL):$AUTH_FAILS"
fi
TOTAL=$((TOTAL+1))

# Get a token for API tests
TOKEN=$(curl -sk -X POST "$BASE/realms/borrowhood/protocol/openid-connect/token" \
  -d "client_id=$KC_CLIENT" \
  -d "grant_type=password" \
  -d "username=angel" \
  -d "password=helix_pass" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  ok "Token obtained for API tests"
else
  fail "Could not get token for API tests"
fi

# ── 4. BorrowHood API ──
section "4. BorrowHood API"

# Items / Marketplace
for endpoint in "/api/v1/items" "/api/v1/listings" "/api/v1/communities"; do
  RESP=$(curl -sk -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE$endpoint" 2>/dev/null)
  CODE=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | sed '$d')
  if [ "$CODE" = "200" ]; then
    ok "GET $endpoint ($CODE)"
  else
    fail "GET $endpoint (expected 200, got $CODE)"
  fi
done

# Rentals
CODE=$(curl -sk -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/rentals" 2>/dev/null)
if [ "$CODE" = "200" ]; then
  ok "GET /api/v1/rentals ($CODE)"
else
  fail "GET /api/v1/rentals (expected 200, got $CODE)"
fi

# ── 5. Database Integrity ──
section "5. Database Integrity (via API)"

# Check item count
ITEM_COUNT=$(curl -sk -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/items?limit=1" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else d.get('total', d.get('count', -1)))" 2>/dev/null)
if [ "$ITEM_COUNT" != "0" ] && [ "$ITEM_COUNT" != "-1" ]; then
  ok "Items exist in database (got response)"
else
  fail "No items found or bad response"
fi

# Check listing count
LISTING_COUNT=$(curl -sk -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/listings?limit=1" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d, list) else d.get('total', d.get('count', -1)))" 2>/dev/null)
if [ "$LISTING_COUNT" != "0" ] && [ "$LISTING_COUNT" != "-1" ]; then
  ok "Listings exist in database (got response)"
else
  fail "No listings found or bad response"
fi

# ── 6. Demo Login Page Content ──
section "6. Demo Login Page Sanity"

DEMO_HTML=$(curl -sk "$BASE/demo-login" 2>/dev/null)

# Check all 14 cast names appear on demo-login
CAST_NAMES="Angel Sally Mike Nino Maria Marco Pietro Jake Rosa George Leonardo John Sofia Anne"
NAMES_OK=0; NAMES_FAIL=0; NAMES_MISSING=""
for name in $CAST_NAMES; do
  if echo "$DEMO_HTML" | grep -q "$name"; then
    NAMES_OK=$((NAMES_OK+1))
  else
    NAMES_FAIL=$((NAMES_FAIL+1))
    NAMES_MISSING="$NAMES_MISSING $name"
  fi
done

if [ "$NAMES_FAIL" -eq 0 ]; then
  ok "All 14 cast names on demo-login page"
else
  fail "Missing from demo-login:$NAMES_MISSING"
fi
TOTAL=$((TOTAL+1))

# Check avatar images are referenced
AVATAR_REFS=$(echo "$DEMO_HTML" | grep -c 'src="/static/images/avatars/' 2>/dev/null || echo "0")
if [ "$AVATAR_REFS" -ge 10 ]; then
  ok "Avatar images referenced ($AVATAR_REFS found)"
else
  fail "Avatar image references: only $AVATAR_REFS (expected 10+)"
fi

# ── 7. Server Health ──
section "7. Server Health"

if [ "$MODE" = "hetzner" ]; then
  # Check container status
  PLATFORM=$(ssh root@46.62.138.218 "docker ps --format '{{.Status}}' -f name=helix-platform" 2>/dev/null)
  if echo "$PLATFORM" | grep -q "healthy"; then
    ok "helix-platform container healthy"
  else
    fail "helix-platform: $PLATFORM"
  fi

  KC_STATUS=$(ssh root@46.62.138.218 "docker ps --format '{{.Status}}' -f name=keycloak" 2>/dev/null)
  if echo "$KC_STATUS" | grep -q "healthy"; then
    ok "keycloak container healthy"
  else
    fail "keycloak: $KC_STATUS"
  fi

  PG_STATUS=$(ssh root@46.62.138.218 "docker ps --format '{{.Status}}' -f name=postgres" 2>/dev/null)
  if echo "$PG_STATUS" | grep -q "healthy"; then
    ok "postgres container healthy"
  else
    fail "postgres: $PG_STATUS"
  fi

  # Check for recent 500 errors
  ERRORS=$(ssh root@46.62.138.218 "docker logs helix-platform --since 10m 2>&1 | grep -cE '\"500\"|Traceback|Internal Server Error' || true" 2>/dev/null | grep -oE '[0-9]+' | tail -1)
  ERRORS="${ERRORS:-0}"
  if [ "$ERRORS" -eq 0 ]; then
    ok "No 500 errors in last 10 minutes"
  else
    fail "$ERRORS errors/tracebacks in last 10 minutes"
  fi
fi

# ── Results ──
echo ""
echo "\033[1;37m╔══════════════════════════════════════════════════╗"
if [ "$FAIL" -eq 0 ]; then
  echo "║  RESULT: ALL $TOTAL CHECKS PASSED                    ║"
else
  echo "║  RESULT: $PASS/$TOTAL passed, $FAIL FAILED                  ║"
fi
echo "╚══════════════════════════════════════════════════╝\033[0m"

exit $FAIL
