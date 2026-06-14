#!/usr/bin/env bash
# ============================================================
# HelixNet / BorrowHood Post-Deploy Smoke Test
# Run after every deploy. Takes ~5 seconds. Catches 500s fast.
#
# Usage:
#   ./scripts/smoke-test.sh              # test local helix-platform (helix.local)
#   ./scripts/smoke-test.sh hetzner      # test Hetzner BorrowHood (borrowhood on 443)
#
# "NEVER say fixed without verifying the output."
# ============================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────
TARGET="${1:-local}"
REALM="borrowhood"          # Keycloak realm to mint the test token against
CONTAINER="borrowhood"      # docker container name for the log/health section
DEMO_LOGIN_EXPECT="200"     # /demo-login: 200 when BH_DEBUG=true, 404 when off
if [[ "$TARGET" == "hetzner" ]]; then
    # Running ON the Hetzner server (via ssh)
    # Caddy listens on 443, routes to BorrowHood
    BASE="https://localhost"
    KC_URL="https://localhost"
    ENV_NAME="HETZNER"
    APP_MODE="borrowhood"
elif [[ "$TARGET" == "hetzner-remote" ]]; then
    # Running FROM local machine through SSH tunnel / public IP
    BASE="https://46.62.138.218"
    KC_URL="https://46.62.138.218"
    ENV_NAME="HETZNER (remote)"
    APP_MODE="borrowhood"
elif [[ "$TARGET" == "prod" ]]; then
    # Prod via the public host. Use this instead of the 'hetzner' (localhost)
    # target -- Caddy only serves TLS for the real SNI, so https://localhost
    # fails the handshake (curl exit 35) and aborts under set -e.
    BASE="https://lapiazza.app"
    KC_URL="https://lapiazza.app"
    REALM="borrowhood"
    CONTAINER="borrowhood"
    ENV_NAME="PROD"
    APP_MODE="borrowhood"
elif [[ "$TARGET" == "staging" ]]; then
    # Staging on Hetzner -- reachable publicly; Caddy path-routes /realms/*.
    # The marketplace staging app lives at staging.lapiazza.app but validates JWTs
    # against the lapiazza-realm-staging realm issued by staging-bottega.lapiazza.app
    # (that's what BH_KC_REALM / BH_KC_URL are set to in the borrowhood_staging
    # container). Mint the token from THAT issuer or the app rejects it -> the
    # false-RED that blocked lp_deploy auto-rollback (#141, fixed 2026-06-14).
    BASE="https://staging.lapiazza.app"
    KC_URL="https://staging-bottega.lapiazza.app"   # the issuer the staging app trusts
    REALM="lapiazza-realm-staging"                   # the realm the staging app validates against
    CONTAINER="borrowhood_staging"
    DEMO_LOGIN_EXPECT="200"   # demo-login is gated on (not debug AND env==prod); staging
                              # is env=staging, so the UAT user-switcher is live -> 200
    ENV_NAME="STAGING"
    APP_MODE="borrowhood"
else
    BASE="https://helix.local"
    KC_URL="https://keycloak.helix.local"
    ENV_NAME="LOCAL"
    APP_MODE="helixnet"
fi

CURL="curl -s -k --max-time 10"
PASS=0
FAIL=0
WARN=0
ERRORS=()

# ── Helpers ────────────────────────────────────────────────
pass() { PASS=$((PASS + 1)); printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { FAIL=$((FAIL + 1)); ERRORS+=("$1"); printf "  \033[31m✗\033[0m %s\n" "$1"; }
warn() { WARN=$((WARN + 1)); printf "  \033[33m!\033[0m %s\n" "$1"; }
section() { printf "\n\033[1;36m── %s ──\033[0m\n" "$1"; }

check_status() {
    local label="$1"
    local url="$2"
    local expected="${3:-200}"
    local headers="${4:-}"

    local code
    if [[ -n "$headers" ]]; then
        code=$($CURL -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$url")
    else
        code=$($CURL -o /dev/null -w "%{http_code}" "$url")
    fi

    if [[ "$code" == "$expected" ]]; then
        pass "$label ($code)"
    elif [[ "$code" == "000" ]]; then
        fail "$label (TIMEOUT - server unreachable)"
    else
        fail "$label (expected $expected, got $code)"
    fi
}

check_json_array() {
    local label="$1"
    local url="$2"

    local body
    body=$($CURL -H "Authorization: Bearer $TOKEN" "$url")
    local code=$?

    if [[ $code -ne 0 ]]; then
        fail "$label (curl failed)"
        return
    fi

    # Check it's a JSON array (starts with [)
    if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        local count
        count=$(echo "$body" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        pass "$label (${count} items)"
    elif echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, dict)" 2>/dev/null; then
        # It's a JSON object -- might be an error or a summary
        local detail
        detail=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('detail','ok'))" 2>/dev/null)
        if [[ "$detail" == "Not authenticated" ]]; then
            fail "$label (auth failed -- token expired?)"
        elif [[ "$detail" == "ok" ]]; then
            pass "$label (object response)"
        else
            fail "$label (error: $detail)"
        fi
    else
        fail "$label (invalid JSON response)"
    fi
}

check_json_object() {
    local label="$1"
    local url="$2"
    local required_key="${3:-}"

    local body
    body=$($CURL -H "Authorization: Bearer $TOKEN" "$url")

    if [[ -n "$required_key" ]]; then
        if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$required_key' in d" 2>/dev/null; then
            local val
            val=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$required_key',''))" 2>/dev/null)
            pass "$label ($required_key: $val)"
        else
            fail "$label (missing key: $required_key)"
        fi
    else
        if echo "$body" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            pass "$label (valid JSON)"
        else
            fail "$label (invalid JSON)"
        fi
    fi
}

# ── Start ──────────────────────────────────────────────────
printf "\033[1;37m"
printf "╔══════════════════════════════════════════════════╗\n"
if [[ "$APP_MODE" == "borrowhood" ]]; then
    printf "║      BorrowHood Post-Deploy Smoke Test          ║\n"
else
    printf "║      HelixNet Post-Deploy Smoke Test            ║\n"
fi
printf "║      Target: %-34s ║\n" "$ENV_NAME ($BASE)"
printf "╚══════════════════════════════════════════════════╝\n"
printf "\033[0m"

# ============================================================
# BORROWHOOD SMOKE TEST (Hetzner)
# ============================================================
if [[ "$APP_MODE" == "borrowhood" ]]; then

    # ── 1. Health Check ──────────────────────────────────────
    section "1. Health Check"
    HEALTH=$($CURL "$BASE/api/v1/health" 2>/dev/null)
    if echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy'" 2>/dev/null; then
        DB_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['checks']['database'])" 2>/dev/null)
        UPTIME=$(echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(int(d['uptime_seconds']))" 2>/dev/null)
        pass "BorrowHood healthy (db: $DB_STATUS, uptime: ${UPTIME}s)"
    else
        fail "BorrowHood health check FAILED"
    fi

    # ── 2. Public HTML Pages ─────────────────────────────────
    section "2. Public HTML Pages"
    check_status "Home page" "$BASE/"
    check_status "Browse page" "$BASE/browse"
    # Fuzzy search exercises func.similarity() -> needs the pg_trgm extension.
    # On 2026-05-27 staging 500'd here because pg_trgm was missing (run_migrations
    # was gated behind BH_DEBUG, which staging runs as false). This check catches
    # that whole class before a human does.
    check_status "Browse + fuzzy search (q=cooky)" "$BASE/browse?q=cooky"
    check_status "Members page" "$BASE/members"
    check_status "Helpboard page" "$BASE/helpboard"
    check_status "Terms page" "$BASE/terms"
    # Demo login is a debug-only route: 200 when BH_DEBUG=true (local, prod),
    # 404 when debug is off (staging). Expect per-env so a healthy staging is green.
    check_status "Demo login page" "$BASE/demo-login" "$DEMO_LOGIN_EXPECT"
    # Onboarding is auth-gated: an anonymous visitor is redirected to /login (302)
    # on every env. (Following the redirect would land on the login page.)
    check_status "Onboarding page (auth redirect)" "$BASE/onboarding" "302"

    # Auth-required pages should redirect (307)
    check_status "Testing dashboard (auth redirect)" "$BASE/testing" "307"
    check_status "Backlog board (auth redirect)" "$BASE/backlog" "307"

    # ── 3. Public API (no auth) ──────────────────────────────
    section "3. Public API (no auth)"
    TOKEN=""  # clear for unauthenticated calls

    ITEMS_BODY=$($CURL "$BASE/api/v1/items" 2>/dev/null)
    if echo "$ITEMS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        ITEM_COUNT=$(echo "$ITEMS_BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        pass "GET /api/v1/items ($ITEM_COUNT items)"
    else
        fail "GET /api/v1/items (bad response)"
    fi

    LISTINGS_BODY=$($CURL "$BASE/api/v1/listings" 2>/dev/null)
    if echo "$LISTINGS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        LISTING_COUNT=$(echo "$LISTINGS_BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        pass "GET /api/v1/listings ($LISTING_COUNT listings)"
    else
        fail "GET /api/v1/listings (bad response)"
    fi

    REVIEWS_BODY=$($CURL "$BASE/api/v1/reviews" 2>/dev/null)
    if echo "$REVIEWS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        REVIEW_COUNT=$(echo "$REVIEWS_BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        pass "GET /api/v1/reviews ($REVIEW_COUNT reviews)"
    else
        fail "GET /api/v1/reviews (bad response)"
    fi

    BADGE_CAT=$($CURL "$BASE/api/v1/badges/catalog" 2>/dev/null)
    if echo "$BADGE_CAT" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        BADGE_COUNT=$(echo "$BADGE_CAT" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
        pass "GET /api/v1/badges/catalog ($BADGE_COUNT badge types)"
    else
        fail "GET /api/v1/badges/catalog (bad response)"
    fi

    USERS_BODY=$($CURL "$BASE/api/v1/users/" 2>/dev/null)
    if echo "$USERS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'items' in d or isinstance(d, list)" 2>/dev/null; then
        USER_COUNT=$(echo "$USERS_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total', len(d)) if isinstance(d, dict) else len(d))")
        pass "GET /api/v1/users ($USER_COUNT users)"
    else
        fail "GET /api/v1/users (bad response)"
    fi

    # ── 4. Keycloak Authentication ───────────────────────────
    section "4. Keycloak Authentication"
    TOKEN_RESPONSE=$($CURL -X POST "$KC_URL/realms/$REALM/protocol/openid-connect/token" \
        -d "client_id=borrowhood-web" \
        -d "grant_type=password" \
        -d "username=angel" \
        -d "password=helix_pass" 2>/dev/null)

    TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

    if [[ -n "$TOKEN" && "$TOKEN" != "" ]]; then
        pass "Keycloak token obtained ($REALM realm)"
    else
        fail "Keycloak token FAILED -- all auth tests will fail"
        ERROR_MSG=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error_description', d.get('error','unknown')))" 2>/dev/null || echo "no response")
        warn "Keycloak error: $ERROR_MSG"
    fi

    # ── 5. Authenticated API ─────────────────────────────────
    section "5. Authenticated API"
    if [[ -n "$TOKEN" ]]; then
        # Rentals
        check_json_array "GET /api/v1/rentals" "$BASE/api/v1/rentals"

        # Notifications
        check_json_object "GET /api/v1/notifications/summary" "$BASE/api/v1/notifications/summary" "total"

        # Badges (user)
        check_json_array "GET /api/v1/badges" "$BASE/api/v1/badges"

        # Bids summary
        BID_SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/bids/summary" 2>/dev/null)
        if echo "$BID_SUMMARY" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            pass "GET /api/v1/bids/summary (valid JSON)"
        else
            fail "GET /api/v1/bids/summary (bad response)"
        fi

        # Deposits
        check_json_array "GET /api/v1/deposits" "$BASE/api/v1/deposits"

        # Disputes
        check_json_array "GET /api/v1/disputes" "$BASE/api/v1/disputes"

        # Helpboard
        check_json_array "GET /api/v1/helpboard/posts" "$BASE/api/v1/helpboard/posts"

        # Favorites
        check_json_array "GET /api/v1/users/me/favorites" "$BASE/api/v1/users/me/favorites"
    else
        warn "Skipping authenticated API tests (no token)"
    fi

    # ── 6. QA Dashboard ──────────────────────────────────────
    section "6. QA Dashboard"
    if [[ -n "$TOKEN" ]]; then
        check_json_array "GET /testing/bugs" "$BASE/api/v1/testing/bugs"
        check_json_array "GET /testing/tests" "$BASE/api/v1/testing/tests"

        SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/testing/summary")
        if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total_tests' in d" 2>/dev/null; then
            TOTAL=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total_tests'])" 2>/dev/null)
            BUGS=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total_bugs'])" 2>/dev/null)
            OPEN=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['open_bugs'])" 2>/dev/null)
            pass "GET /testing/summary (tests: $TOTAL, bugs: $BUGS, open: $OPEN)"
        else
            fail "GET /testing/summary (bad response)"
        fi
    else
        warn "Skipping QA tests (no token)"
    fi

    # ── 7. Backlog Board ─────────────────────────────────────
    section "7. Backlog Board"
    if [[ -n "$TOKEN" ]]; then
        check_json_array "GET /backlog/items" "$BASE/api/v1/backlog/items"

        SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/backlog/summary")
        if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total' in d" 2>/dev/null; then
            TOTAL=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total'])" 2>/dev/null)
            DONE=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['done'])" 2>/dev/null)
            IN_PROG=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['in_progress'])" 2>/dev/null)
            PENDING=$(echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['pending'])" 2>/dev/null)
            pass "GET /backlog/summary (total: $TOTAL, done: $DONE, in_progress: $IN_PROG, pending: $PENDING)"
        else
            fail "GET /backlog/summary (bad response)"
        fi
    else
        warn "Skipping backlog tests (no token)"
    fi

    # ── 8. Container & Log Health ────────────────────────────
    section "8. Container & Log Health"
    if command -v docker &>/dev/null; then
        # Check key containers are running
        for svc in "$CONTAINER" caddy keycloak postgres redis; do
            STATUS=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "missing")
            if [[ "$STATUS" == "running" ]]; then
                pass "$svc container running"
            else
                fail "$svc container NOT running (status: $STATUS)"
            fi
        done

        # Check for crash-looping containers
        RESTARTING=$(docker ps --format '{{.Names}} {{.Status}}' | grep -i "restarting" || true)
        if [[ -n "$RESTARTING" ]]; then
            warn "Crash-looping containers: $RESTARTING"
        else
            pass "No crash-looping containers"
        fi

        # Check BorrowHood logs for errors
        RECENT_ERRORS=$(docker logs "$CONTAINER" --tail 30 2>&1 | grep -ci "500\|traceback\|error.*exception" || true)
        if [[ "$RECENT_ERRORS" -eq 0 ]]; then
            pass "No 500s or tracebacks in BorrowHood logs"
        else
            warn "Found $RECENT_ERRORS error indicators in last 30 log lines"
        fi
    else
        warn "Docker not available -- skipping container checks"
    fi

# ============================================================
# HELIXNET SMOKE TEST (Local)
# ============================================================
else

    # ── 1. Health Checks (no auth needed) ─────────────────────
    section "1. Health Checks"
    check_status "Platform healthz" "$BASE/health/healthz"
    check_status "QA health-check" "$BASE/api/v1/testing/health-check"

    # ── 2. HTML Pages (no auth needed) ────────────────────────
    section "2. HTML Pages"
    check_status "QA Login page" "$BASE/testing/login"
    check_status "Training page" "$BASE/training"
    check_status "How to Report" "$BASE/how-to-report-bugs"
    check_status "Backlog board" "$BASE/backlog"
    check_status "Camper dashboard" "$BASE/camper/dashboard"
    check_status "ISTQB PDF" "$BASE/static/training/ISTQB_CTFL_Syllabus_v4.0.1.pdf"

    # ── 3. Get Auth Token ─────────────────────────────────────
    section "3. Authentication"
    TOKEN_RESPONSE=$($CURL -X POST "$KC_URL/realms/kc-camper-service-realm-dev/protocol/openid-connect/token" \
        -d "client_id=camper_service_web" \
        -d "grant_type=password" \
        -d "username=angel" \
        -d "password=helix_pass" 2>/dev/null)

    TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

    if [[ -n "$TOKEN" && "$TOKEN" != "" ]]; then
        pass "Keycloak token obtained"
    else
        fail "Keycloak token FAILED -- all auth tests will fail"
        ERROR_MSG=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error_description', d.get('error','unknown')))" 2>/dev/null || echo "no response")
        warn "Keycloak error: $ERROR_MSG"
    fi

    # ── 4. QA Testing API ─────────────────────────────────────
    section "4. QA Testing API"
    if [[ -n "$TOKEN" ]]; then
        check_json_array "GET /testing/bugs" "$BASE/api/v1/testing/bugs"
        check_json_array "GET /testing/bugs?application=helixnet" "$BASE/api/v1/testing/bugs?application=helixnet"
        check_json_array "GET /testing/tests" "$BASE/api/v1/testing/tests"

        SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/testing/summary")
        if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total_tests' in d and 'bugs_by_application' in d" 2>/dev/null; then
            pass "GET /testing/summary (valid, has bugs_by_application)"
        else
            fail "GET /testing/summary (bad response)"
        fi
    else
        warn "Skipping QA API tests (no token)"
    fi

    # ── 5. Backlog API ─────────────────────────────────────────
    section "5. Backlog API"
    if [[ -n "$TOKEN" ]]; then
        check_json_array "GET /backlog/items" "$BASE/api/v1/backlog/items"
        check_json_array "GET /backlog/items?application=helixnet" "$BASE/api/v1/backlog/items?application=helixnet"

        SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/backlog/summary")
        if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total' in d and 'by_application' in d" 2>/dev/null; then
            pass "GET /backlog/summary (valid, has by_application)"
        else
            fail "GET /backlog/summary (bad response)"
        fi
    else
        warn "Skipping Backlog API tests (no token)"
    fi

    # ── 6. Camper API ──────────────────────────────────────────
    section "6. Camper API"
    if [[ -n "$TOKEN" ]]; then
        check_json_array "GET /camper/vehicles" "$BASE/api/v1/camper/vehicles"
        check_json_array "GET /camper/customers" "$BASE/api/v1/camper/customers"
        check_json_array "GET /camper/jobs" "$BASE/api/v1/camper/jobs"
        check_json_array "GET /camper/bays" "$BASE/api/v1/camper/bays"
        check_json_array "GET /camper/quotations" "$BASE/api/v1/camper/quotations"
        check_json_array "GET /camper/invoices" "$BASE/api/v1/camper/invoices"
        check_json_array "GET /camper/appointments" "$BASE/api/v1/camper/appointments"

        # Vehicle search (BUG-016 phone sync check)
        SEARCH=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/camper/vehicles/search?q=kenel")
        if echo "$SEARCH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
            PHONE=$(echo "$SEARCH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('owner_phone','') if d else 'no results')" 2>/dev/null)
            if [[ "$PHONE" == *"828"* ]]; then
                pass "Vehicle search 'kenel' (phone synced: $PHONE)"
            elif [[ "$PHONE" == "no results" ]]; then
                warn "Vehicle search 'kenel' (no results -- seed data missing?)"
            else
                warn "Vehicle search 'kenel' (phone may be stale: $PHONE)"
            fi
        else
            fail "Vehicle search 'kenel' (bad response)"
        fi

        # Job activities
        JOB_ID=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/camper/jobs" | \
            python3 -c "import sys,json; jobs=json.load(sys.stdin); print(jobs[0]['id'] if jobs else '')" 2>/dev/null)
        if [[ -n "$JOB_ID" ]]; then
            check_json_array "GET /camper/jobs/{id}/activities" "$BASE/api/v1/camper/jobs/$JOB_ID/activities"
        else
            warn "No jobs found -- skipping activity trail test"
        fi

        # Dashboard summary
        DASH=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/camper/dashboard/summary")
        if echo "$DASH" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            pass "GET /camper/dashboard/summary (valid JSON)"
        else
            fail "GET /camper/dashboard/summary (bad response)"
        fi
    else
        warn "Skipping Camper API tests (no token)"
    fi

    # ── 7. ISOTTO Print Shop API ──────────────────────────────
    section "7. ISOTTO Print Shop API"

    ISOTTO_TOKEN_RESPONSE=$($CURL -X POST "$KC_URL/realms/kc-isotto-print-realm-dev/protocol/openid-connect/token" \
        -d "client_id=isotto_print_web" \
        -d "grant_type=password" \
        -d "username=famousguy" \
        -d "password=helix_pass" 2>/dev/null)

    ISOTTO_TOKEN=$(echo "$ISOTTO_TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

    if [[ -n "$ISOTTO_TOKEN" && "$ISOTTO_TOKEN" != "" ]]; then
        pass "ISOTTO Keycloak token obtained"

        # HTML pages
        check_status "Print Shop login page" "$BASE/print-shop"
        check_status "Print Shop dashboard" "$BASE/print-shop/dashboard"
        check_status "Print Shop orders page" "$BASE/print-shop/orders"
        check_status "Print Shop customers page" "$BASE/print-shop/customers"
        check_status "Print Shop invoices page" "$BASE/print-shop/invoices"

        ORIG_TOKEN="$TOKEN"
        TOKEN="$ISOTTO_TOKEN"

        # API endpoints
        check_json_array "GET /print-shop/customers" "$BASE/api/v1/print-shop/customers"
        check_json_array "GET /print-shop/orders" "$BASE/api/v1/print-shop/orders"
        check_json_array "GET /print-shop/invoices" "$BASE/api/v1/print-shop/invoices"

        # Dashboard
        ISOTTO_DASH=$($CURL -H "Authorization: Bearer $ISOTTO_TOKEN" "$BASE/api/v1/print-shop/dashboard")
        if echo "$ISOTTO_DASH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'orders_in_production' in d" 2>/dev/null; then
            PENDING_INV=$(echo "$ISOTTO_DASH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pending_invoices', '?'))" 2>/dev/null)
            pass "GET /print-shop/dashboard (pending_invoices: $PENDING_INV)"
        else
            fail "GET /print-shop/dashboard (bad response)"
        fi

        # Sprint 2-3: Catalog pages
        check_status "Print Shop catalog page" "$BASE/print-shop/catalog"
        check_status "Print Shop suppliers page" "$BASE/print-shop/suppliers"
        check_status "Print Shop purchase orders page" "$BASE/print-shop/purchase-orders"
        check_status "Print Shop artworks page" "$BASE/print-shop/artworks"
        check_status "Print Shop print queue page" "$BASE/print-shop/print-queue"

        # Catalog API
        check_json_array "GET /catalog/suppliers" "$BASE/api/v1/print-shop/catalog/suppliers"
        check_json_array "GET /catalog/products" "$BASE/api/v1/print-shop/catalog/products"
        check_json_array "GET /catalog/purchase-orders" "$BASE/api/v1/print-shop/catalog/purchase-orders"
        check_json_array "GET /catalog/artworks" "$BASE/api/v1/print-shop/catalog/artworks"

        # Print queue
        PRINT_QUEUE=$($CURL -H "Authorization: Bearer $ISOTTO_TOKEN" "$BASE/api/v1/print-shop/print-queue")
        if echo "$PRINT_QUEUE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total_items' in d" 2>/dev/null; then
            PQ_ITEMS=$(echo "$PRINT_QUEUE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total_items'])" 2>/dev/null)
            pass "GET /print-queue ($PQ_ITEMS items)"
        else
            fail "GET /print-queue (bad response)"
        fi

        TOKEN="$ORIG_TOKEN"
    else
        fail "ISOTTO Keycloak token FAILED -- skipping print shop tests"
        check_status "Print Shop login page" "$BASE/print-shop"
    fi

    # ── 8. Server Logs Check ──────────────────────────────────
    section "8. Server Logs (last 30 lines)"
    if command -v docker &>/dev/null; then
        RECENT_ERRORS=$(docker logs helix-platform --tail 30 2>&1 | grep -ci "500\|traceback\|error.*exception" || true)
        if [[ "$RECENT_ERRORS" -eq 0 ]]; then
            pass "No 500s or tracebacks in recent logs"
        else
            warn "Found $RECENT_ERRORS error indicators in last 30 log lines"
        fi
    elif [[ "$ENV_NAME" == "HETZNER" ]]; then
        warn "Cannot check Hetzner logs from this script (run on server)"
    else
        warn "Docker not available -- skipping log check"
    fi

fi

# ── Results ────────────────────────────────────────────────
printf "\n\033[1;37m"
printf "══════════════════════════════════════════════════\n"
printf "  RESULTS: "
printf "\033[32m%d passed\033[1;37m  " "$PASS"
if [[ $FAIL -gt 0 ]]; then
    printf "\033[31m%d FAILED\033[1;37m  " "$FAIL"
else
    printf "0 failed  "
fi
if [[ $WARN -gt 0 ]]; then
    printf "\033[33m%d warnings\033[1;37m" "$WARN"
else
    printf "0 warnings"
fi
printf "\n══════════════════════════════════════════════════\n"
printf "\033[0m"

if [[ $FAIL -gt 0 ]]; then
    printf "\n\033[31mFAILED CHECKS:\033[0m\n"
    for err in "${ERRORS[@]}"; do
        printf "  - %s\n" "$err"
    done
    printf "\n"
    exit 1
else
    if [[ $WARN -gt 0 ]]; then
        printf "\n\033[33mDeploy OK with warnings. Check the items above.\033[0m\n\n"
    else
        printf "\n\033[32mAll clear. Ship it.\033[0m\n\n"
    fi
    exit 0
fi
