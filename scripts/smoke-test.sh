#!/usr/bin/env bash
# ============================================================
# HelixNet Post-Deploy Smoke Test
# Run after every deploy. Takes ~5 seconds. Catches 500s fast.
#
# Usage:
#   ./scripts/smoke-test.sh              # test local (helix.local)
#   ./scripts/smoke-test.sh hetzner      # test Hetzner (46.62.138.218:8081)
#
# "NEVER say fixed without verifying the output."
# ============================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────
TARGET="${1:-local}"
if [[ "$TARGET" == "hetzner" ]]; then
    # Running ON the Hetzner server (via ssh)
    # Traefik listens on 443 inside the server
    BASE="https://localhost"
    KC_URL="https://localhost"
    ENV_NAME="HETZNER"
elif [[ "$TARGET" == "hetzner-remote" ]]; then
    # Running FROM local machine through SSH tunnel / public IP
    BASE="https://46.62.138.218:8081"
    KC_URL="https://46.62.138.218:8081"
    ENV_NAME="HETZNER (remote)"
else
    BASE="https://helix.local"
    KC_URL="https://keycloak.helix.local"
    ENV_NAME="LOCAL"
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

# ── Start ──────────────────────────────────────────────────
printf "\033[1;37m"
printf "╔══════════════════════════════════════════════════╗\n"
printf "║      HelixNet Post-Deploy Smoke Test            ║\n"
printf "║      Target: %-34s ║\n" "$ENV_NAME ($BASE)"
printf "╚══════════════════════════════════════════════════╝\n"
printf "\033[0m"

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
    # Try to show the error
    ERROR_MSG=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error_description', d.get('error','unknown')))" 2>/dev/null || echo "no response")
    warn "Keycloak error: $ERROR_MSG"
fi

# ── 4. QA Testing API ─────────────────────────────────────
section "4. QA Testing API"
if [[ -n "$TOKEN" ]]; then
    check_json_array "GET /testing/bugs" "$BASE/api/v1/testing/bugs"
    check_json_array "GET /testing/tests" "$BASE/api/v1/testing/tests"

    # Summary is an object, not array
    SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/testing/summary")
    if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total_tests' in d or 'total_bugs' in d" 2>/dev/null; then
        pass "GET /testing/summary (valid)"
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

    SUMMARY=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/backlog/summary")
    if echo "$SUMMARY" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'total' in d" 2>/dev/null; then
        pass "GET /backlog/summary (valid)"
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

    # Test vehicle search (the check-in flow)
    SEARCH=$($CURL -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/camper/vehicles/search?q=kenel")
    if echo "$SEARCH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list)" 2>/dev/null; then
        # Verify the phone fix (BUG-016)
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

    # Test job activities (BL-011)
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

# ── 7. Server Logs Check ──────────────────────────────────
section "7. Server Logs (last 30 lines)"
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
