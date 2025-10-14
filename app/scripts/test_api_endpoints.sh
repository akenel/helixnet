#!/bin/bash
# A simple script to check API health and basic user creation (Integration Test)

API_HOST="https://helix.local"
API_PREFIX="/api/v1" # Define the versioned API prefix for clarity
# Note: Using '-k' to bypass local self-signed certificate errors.

# Variables to store test results
ACCESS_TOKEN=""

echo "--- 🚀 Starting Basic API Checks ---"

# 1. Traefik/Base Check
echo "Checking base connectivity via Traefik at ${API_HOST}/"
STATUS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" "${API_HOST}/")

if [ "$STATUS_CODE" -eq 200 ] || [ "$STATUS_CODE" -eq 307 ] || [ "$STATUS_CODE" -eq 404 ]; then
    echo "✅ Base Check: Success (Status ${STATUS_CODE}). Connectivity looks good."
else
    echo "❌ Base Check: Failed (Status ${STATUS_CODE}). Traefik routing may still be misconfigured."
    exit 1
fi

# 2. Check the FastAPI Documentation endpoint (/docs) - NOT versioned
ENDPOINT="/docs"
echo "Checking FastAPI documentation endpoint: ${API_HOST}${ENDPOINT}"
RESPONSE=$(curl -s -k -o /dev/null -w "%{http_code}" "${API_HOST}${ENDPOINT}")
HTTP_CODE=$RESPONSE

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ /docs Check: Success (Status 200 OK). FastAPI is running and routing correctly."
else
    echo "❌ /docs Check: Failed (Status ${HTTP_CODE}). This suggests the main app structure or middleware is incorrect."
fi

# --- AUTHENTICATION FLOW (Steps 3 & 4) ---

# 3. FIX: Authentication Login Endpoint (POST /auth/login)
# Test for the login flow using credentials for a seeded user (admin/admin from .env is assumed)
AUTH_ENDPOINT="${API_PREFIX}/auth/login"
echo "Checking Auth Login Endpoint: ${API_HOST}${AUTH_ENDPOINT} (POST request with credentials)"

# IMPORTANT: The OAuth2PasswordRequestForm expects data in 'application/x-www-form-urlencoded' format
# We are using dummy 'admin' credentials.
AUTH_RESPONSE=$(curl -s -k -X POST -w "\n%{http_code}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@helix.net&password=admin" \
    "${API_HOST}${AUTH_ENDPOINT}")

AUTH_HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n 1)
AUTH_BODY=$(echo "$AUTH_RESPONSE" | head -n -1)

if [ "$AUTH_HTTP_CODE" -eq 200 ]; then
    echo "✅ /auth/login POST Check: SUCCESS (Status 200 OK)."
    # Extract the access token for the next step
    ACCESS_TOKEN=$(echo "$AUTH_BODY" | grep -o '"access_token": *"[^"]*"' | head -n 1 | sed 's/"access_token": *//;s/"//g')
    echo "   Access Token acquired for next check."
elif [ "$AUTH_HTTP_CODE" -eq 401 ]; then
    echo "❌ /auth/login POST Check: FAILED (Status 401 Unauthorized)."
    echo "   Credentials (admin@helix.net/admin) failed. Check 'seed_users.py' or 'login' logic."
elif [ "$AUTH_HTTP_CODE" -eq 404 ]; then
    echo "❌ /auth/login POST Check: FAILED (Status 404 Not Found)."
    echo "   Path is still incorrect. Expected path: ${API_HOST}${AUTH_ENDPOINT}"
else
    echo "⚠️ /auth/login POST Check: Unexpected Status ${AUTH_HTTP_CODE}"
    echo "   Full Response Body:"
    echo "$AUTH_BODY"
fi

# 4. Authenticated GET /jobs endpoint check
ENDPOINT="${API_PREFIX}/jobs"
echo "Checking application endpoint: ${API_HOST}${ENDPOINT} (GET request, Authenticated)"

if [ -z "$ACCESS_TOKEN" ]; then
    echo "⏩ Skipping authenticated check for ${ENDPOINT} as login failed."
else
    # Making the GET request with the acquired token in the Authorization header
    JOBS_RESPONSE=$(curl -s -k -w "\n%{http_code}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        "${API_HOST}${ENDPOINT}")
    
    JOBS_HTTP_CODE=$(echo "$JOBS_RESPONSE" | tail -n 1)
    JOBS_BODY=$(echo "$JOBS_RESPONSE" | head -n -1)

    if [ "$JOBS_HTTP_CODE" -eq 200 ]; then
        echo "✅ /jobs Endpoint Check: Success (Status 200 OK)"
        echo "   Response Snippet (first 200 chars):"
        echo "$JOBS_BODY" | head -c 200
    elif [ "$JOBS_HTTP_CODE" -eq 401 ]; then
        echo "❌ /jobs Endpoint Check: Failed (Status 401 Unauthorized) - Token may be invalid/expired."
    elif [ "$JOBS_HTTP_CODE" -eq 404 ]; then
        echo "❌ /jobs Endpoint Check: Not Found (Status 404). Router registration issue in main.py is likely."
        echo "   NOTE: This path should map to the @jobs_router.get('/jobs') function."
    else
        echo "⚠️ /jobs Endpoint Check: Unexpected Status ${JOBS_HTTP_CODE}"
        echo "   Full Response Body:"
        echo "$JOBS_BODY"
    fi
fi

echo "--- ✅ Basic API Checks Complete ---"
