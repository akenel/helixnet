#!/bin/bash
# HelixNET UAT Health Check
# BLQ: Quick system status before testing

echo "================================================"
echo "  HelixNET Health Check - $(date '+%Y-%m-%d %H:%M')"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local expected=$3

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$status" == "$expected" ]; then
        echo -e "  [${GREEN}OK${NC}] $name ($status)"
        return 0
    else
        echo -e "  [${RED}FAIL${NC}] $name (got $status, expected $expected)"
        return 1
    fi
}

check_container() {
    local name=$1

    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        health=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null)
        if [ "$health" == "healthy" ]; then
            echo -e "  [${GREEN}OK${NC}] $name (healthy)"
        elif [ -z "$health" ]; then
            echo -e "  [${YELLOW}~~${NC}] $name (running, no health check)"
        else
            echo -e "  [${YELLOW}~~${NC}] $name ($health)"
        fi
        return 0
    else
        echo -e "  [${RED}FAIL${NC}] $name (not running)"
        return 1
    fi
}

echo "CONTAINERS:"
check_container "helix-platform"
check_container "keycloak"
check_container "postgres"
check_container "rabbitmq"
check_container "redis"
check_container "traefik"
echo ""

echo "ENDPOINTS:"
check_service "POS Login" "http://localhost:9003/pos" "200"
check_service "POS Dashboard" "http://localhost:9003/pos/dashboard" "200"
check_service "POS Search" "http://localhost:9003/pos/search" "200"
check_service "Customer Lookup" "http://localhost:9003/pos/customer-lookup" "200"
check_service "KB Approvals" "http://localhost:9003/pos/kb-approvals" "200"
check_service "Cash Count" "http://localhost:9003/pos/cash-count" "200"
check_service "API Config" "http://localhost:9003/api/v1/pos/config" "200"
echo ""

echo "DATABASE:"
customer_count=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM customers" 2>/dev/null | tr -d ' ')
product_count=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM products" 2>/dev/null | tr -d ' ')
kb_count=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM kb_contributions" 2>/dev/null | tr -d ' ')

echo "  Customers: $customer_count"
echo "  Products: $product_count"
echo "  KBs: $kb_count"
echo ""

echo "KEYCLOAK REALMS:"
realms=$(docker exec keycloak /opt/keycloak/bin/kcadm.sh get realms --server http://localhost:8080 --realm master --user helix_user --password helix_pass 2>/dev/null | grep -o '"realm" : "[^"]*"' | cut -d'"' -f4 | tr '\n' ', ')
echo "  Active: $realms"
echo ""

echo "================================================"
echo "  Health check complete"
echo "================================================"
