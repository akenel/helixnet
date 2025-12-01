#!/bin/bash
# ============================================================
# HelixNET E2E Test Suite - BLQ Edition
# "Be water, my friend" - Run after every nuke/change
# ============================================================
# Usage: ./e2e-test.sh [--json] [--quick]
#   --json  Output results as JSON (for CI/CD)
#   --quick Skip slow tests (container builds)
# ============================================================

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
SKIP=0
RESULTS=()

# Parse args
JSON_OUTPUT=false
QUICK_MODE=false
for arg in "$@"; do
    case $arg in
        --json) JSON_OUTPUT=true ;;
        --quick) QUICK_MODE=true ;;
    esac
done

# Test functions
log_test() {
    local name="$1"
    local status="$2"
    local detail="$3"

    if [ "$JSON_OUTPUT" = true ]; then
        RESULTS+=("{\"test\":\"$name\",\"status\":\"$status\",\"detail\":\"$detail\"}")
    else
        case $status in
            PASS) echo -e "  [${GREEN}PASS${NC}] $name ${detail:+- $detail}" ;;
            FAIL) echo -e "  [${RED}FAIL${NC}] $name ${detail:+- $detail}" ;;
            SKIP) echo -e "  [${YELLOW}SKIP${NC}] $name ${detail:+- $detail}" ;;
        esac
    fi

    case $status in
        PASS) ((PASS++)) ;;
        FAIL) ((FAIL++)) ;;
        SKIP) ((SKIP++)) ;;
    esac
}

section() {
    if [ "$JSON_OUTPUT" = false ]; then
        echo ""
        echo -e "${BLUE}=== $1 ===${NC}"
    fi
}

# ============================================================
# TEST SUITE
# ============================================================

run_tests() {
    local START_TIME=$(date +%s)

    if [ "$JSON_OUTPUT" = false ]; then
        echo "================================================"
        echo "  HelixNET E2E Test Suite"
        echo "  $(date '+%Y-%m-%d %H:%M:%S')"
        echo "================================================"
    fi

    # ------------------------------------------------------------
    # 1. CONTAINER HEALTH
    # ------------------------------------------------------------
    section "Container Health"

    REQUIRED_CONTAINERS="helix-platform keycloak postgres redis rabbitmq traefik"
    for container in $REQUIRED_CONTAINERS; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")
        if [ "$status" = "healthy" ]; then
            log_test "container:$container" "PASS" "healthy"
        elif [ "$status" = "not_found" ]; then
            log_test "container:$container" "FAIL" "not found"
        else
            log_test "container:$container" "FAIL" "$status"
        fi
    done

    # ------------------------------------------------------------
    # 2. ENVIRONMENT CONFIG
    # ------------------------------------------------------------
    section "Environment Config"

    # Check KEYCLOAK_REALM is artemis
    KC_REALM=$(docker exec helix-platform env 2>/dev/null | grep "^KEYCLOAK_REALM=" | cut -d'=' -f2)
    if [ "$KC_REALM" = "artemis" ]; then
        log_test "env:KEYCLOAK_REALM" "PASS" "artemis"
    else
        log_test "env:KEYCLOAK_REALM" "FAIL" "expected artemis, got $KC_REALM"
    fi

    # ------------------------------------------------------------
    # 3. API ENDPOINTS (Unauthenticated)
    # ------------------------------------------------------------
    section "API Endpoints (Public)"

    # Health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9003/health/healthz" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        log_test "api:health" "PASS" "200 OK"
    else
        log_test "api:health" "FAIL" "HTTP $HTTP_CODE"
    fi

    # Products endpoint (public)
    PRODUCTS=$(curl -s "http://localhost:9003/api/v1/products/?limit=1" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('items',d)) if isinstance(d,dict) else len(d))" 2>/dev/null || echo "0")
    if [ "$PRODUCTS" -gt "0" ]; then
        log_test "api:products" "PASS" "products accessible"
    else
        log_test "api:products" "FAIL" "no products returned"
    fi

    # ------------------------------------------------------------
    # 4. KEYCLOAK AUTHENTICATION
    # ------------------------------------------------------------
    section "Keycloak Authentication"

    # Test user logins
    USERS="pam felix ralph leandra"
    for user in $USERS; do
        TOKEN=$(docker run --rm --network helixnet_core curlimages/curl -s -X POST \
            "http://keycloak:8080/realms/artemis/protocol/openid-connect/token" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "client_id=artemis_pos" \
            -d "username=$user" \
            -d "password=helix_pass" \
            -d "grant_type=password" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token','')[:20])" 2>/dev/null || echo "")

        if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
            log_test "auth:$user" "PASS" "token obtained"
        else
            log_test "auth:$user" "FAIL" "login failed"
        fi
    done

    # Wrong password test
    BAD_TOKEN=$(docker run --rm --network helixnet_core curlimages/curl -s -X POST \
        "http://keycloak:8080/realms/artemis/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "client_id=artemis_pos" \
        -d "username=pam" \
        -d "password=wrong_password" \
        -d "grant_type=password" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('error' if 'error' in d else 'token')" 2>/dev/null || echo "error")

    if [ "$BAD_TOKEN" = "error" ]; then
        log_test "auth:wrong_password" "PASS" "correctly rejected"
    else
        log_test "auth:wrong_password" "FAIL" "should reject bad password"
    fi

    # ------------------------------------------------------------
    # 5. AUTHENTICATED API (Customer/CRACK)
    # ------------------------------------------------------------
    section "Authenticated API (CRACK)"

    # Get Pam's token for authenticated tests
    PAM_TOKEN=$(docker run --rm --network helixnet_core curlimages/curl -s -X POST \
        "http://keycloak:8080/realms/artemis/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "client_id=artemis_pos" \
        -d "username=pam" \
        -d "password=helix_pass" \
        -d "grant_type=password" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

    if [ -n "$PAM_TOKEN" ] && [ "$PAM_TOKEN" != "None" ]; then
        # Customer search
        CUSTOMERS=$(curl -s "http://localhost:9003/api/v1/customers/search?q=@" \
            -H "Authorization: Bearer $PAM_TOKEN" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")

        if [ "$CUSTOMERS" -gt "0" ]; then
            log_test "api:customer_search" "PASS" "$CUSTOMERS customers"
        else
            log_test "api:customer_search" "FAIL" "no customers returned"
        fi

        # Customer search validation (min 1 char)
        VALIDATION=$(curl -s "http://localhost:9003/api/v1/customers/search?q=" \
            -H "Authorization: Bearer $PAM_TOKEN" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print('validated' if 'detail' in d else 'no_validation')" 2>/dev/null || echo "error")

        if [ "$VALIDATION" = "validated" ]; then
            log_test "api:customer_validation" "PASS" "input validated"
        else
            log_test "api:customer_validation" "FAIL" "missing validation"
        fi

        # Unauthorized request (no token)
        UNAUTH=$(curl -s "http://localhost:9003/api/v1/customers/search?q=test" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print('rejected' if d.get('detail')=='Not authenticated' else 'allowed')" 2>/dev/null || echo "error")

        if [ "$UNAUTH" = "rejected" ]; then
            log_test "api:auth_required" "PASS" "correctly requires auth"
        else
            log_test "api:auth_required" "FAIL" "should require auth"
        fi
    else
        log_test "api:customer_search" "SKIP" "no token"
        log_test "api:customer_validation" "SKIP" "no token"
        log_test "api:auth_required" "SKIP" "no token"
    fi

    # ------------------------------------------------------------
    # 6. DATABASE INTEGRITY
    # ------------------------------------------------------------
    section "Database Integrity"

    # Product count (using helix_user and helix_db)
    # Note: After full nuke, only ~18 demo products exist. After safe nuke, 7000+ persist.
    PRODUCT_COUNT=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM products;" 2>/dev/null | tr -d ' \n')
    if [ -n "$PRODUCT_COUNT" ] && [ "$PRODUCT_COUNT" -gt "10" ] 2>/dev/null; then
        log_test "db:products" "PASS" "$PRODUCT_COUNT products"
    elif [ -n "$PRODUCT_COUNT" ]; then
        log_test "db:products" "FAIL" "only $PRODUCT_COUNT products"
    else
        log_test "db:products" "FAIL" "query failed"
    fi

    # Customer count
    CUSTOMER_COUNT=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | tr -d ' \n')
    if [ -n "$CUSTOMER_COUNT" ] && [ "$CUSTOMER_COUNT" -gt "0" ] 2>/dev/null; then
        log_test "db:customers" "PASS" "$CUSTOMER_COUNT customers"
    elif [ -n "$CUSTOMER_COUNT" ]; then
        log_test "db:customers" "FAIL" "no customers"
    else
        log_test "db:customers" "FAIL" "query failed"
    fi

    # KB count
    KB_COUNT=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM kb_contributions;" 2>/dev/null | tr -d ' \n')
    if [ -n "$KB_COUNT" ] && [ "$KB_COUNT" -ge "0" ] 2>/dev/null; then
        log_test "db:kb_contributions" "PASS" "$KB_COUNT KBs"
    else
        log_test "db:kb_contributions" "FAIL" "table missing or query failed"
    fi

    # ------------------------------------------------------------
    # 7. KEYCLOAK REALMS
    # ------------------------------------------------------------
    section "Keycloak Realms"

    REQUIRED_REALMS="artemis blowup fourtwenty"
    for realm in $REQUIRED_REALMS; do
        REALM_EXISTS=$(docker run --rm --network helixnet_core curlimages/curl -s \
            "http://keycloak:8080/realms/$realm/.well-known/openid-configuration" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print('exists' if 'issuer' in d else 'missing')" 2>/dev/null || echo "missing")

        if [ "$REALM_EXISTS" = "exists" ]; then
            log_test "realm:$realm" "PASS" "active"
        else
            log_test "realm:$realm" "FAIL" "not found"
        fi
    done

    # ------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------
    local END_TIME=$(date +%s)
    local DURATION=$((END_TIME - START_TIME))

    if [ "$JSON_OUTPUT" = true ]; then
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"duration_seconds\": $DURATION,"
        echo "  \"summary\": {\"pass\": $PASS, \"fail\": $FAIL, \"skip\": $SKIP},"
        echo "  \"tests\": [$(IFS=,; echo "${RESULTS[*]}")]"
        echo "}"
    else
        echo ""
        echo "================================================"
        echo "  SUMMARY: ${GREEN}$PASS PASS${NC} | ${RED}$FAIL FAIL${NC} | ${YELLOW}$SKIP SKIP${NC}"
        echo "  Duration: ${DURATION}s"
        echo "================================================"

        if [ $FAIL -gt 0 ]; then
            echo -e "  ${RED}E2E TESTS FAILED${NC}"
            exit 1
        else
            echo -e "  ${GREEN}ALL E2E TESTS PASSED${NC}"
            exit 0
        fi
    fi
}

# Run tests
run_tests
