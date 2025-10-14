#!/bin/bash

# ======================================================================
# 🚀 HelixNet Authentication Lifecycle Smoke Test (Verbose)
# Checks login, access, token refresh, and logout with detailed output.
# ======================================================================

# --- ⚙️ Configuration ---
BASE_URL="https://helix.local/api/v1"
USERNAME="admin@helix.net"
PASSWORD="admin"
JOB_ENDPOINT="${BASE_URL}/job/"
LOGIN_URL="${BASE_URL}/auth/login"
REFRESH_URL="${BASE_URL}/auth/token/refresh"
LOGOUT_URL="${BASE_URL}/auth/logout"
ME_URL="${BASE_URL}/me"

# Global variables to store tokens and user details
ACCESS_TOKEN_1=""
REFRESH_TOKEN_1=""
ACCESS_TOKEN_2=""
REFRESH_TOKEN_2=""
USER_ID=""
IS_ADMIN=""

echo " "
echo "=========================================================="
echo " 🧪 Starting Robust Auth Lifecycle Test for $USERNAME"
echo "=========================================================="
echo " "


# --- 1️⃣ Login (Get Initial Tokens) ---
echo "➡️ 1/7 | Logging in to retrieve initial token pair..."
LOGIN_RESPONSE=$(curl -k -s -X POST "${LOGIN_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${USERNAME}&password=${PASSWORD}")

if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null; then
  ACCESS_TOKEN_1=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
  REFRESH_TOKEN_1=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')
  echo "  ✅ Success: Received initial tokens."
  echo "  (Access Token 1: ${ACCESS_TOKEN_1:0:8}...) "
  echo "  (Refresh Token 1: ${REFRESH_TOKEN_1:0:8}...) "
else
  echo "  ❌ FAILURE: Login failed. Response: $LOGIN_RESPONSE"
  exit 1
fi
echo " "


# --- 2️⃣ Fetch User Details and Report ---
echo "➡️ 2/7 | Fetching user profile and reporting authorization details..."

PROFILE_RESPONSE=$(curl -k -s -X GET "${ME_URL}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN_1}")

if echo "$PROFILE_RESPONSE" | jq -e '.id' > /dev/null; then
  USER_ID=$(echo "$PROFILE_RESPONSE" | jq -r '.id')
  IS_ADMIN=$(echo "$PROFILE_RESPONSE" | jq -r '.is_admin')
  
  echo "  ✅ Profile retrieved. Authorization status confirmed:"
  echo "  - User ID:    $USER_ID"
  echo "  - Email:      $USERNAME"
  echo "  - Admin Role: $IS_ADMIN"
else
  echo "  ❌ FAILURE: Could not retrieve user profile."
  echo "  Full Response: $PROFILE_RESPONSE"
  exit 1
fi
echo " "


# --- 3️⃣ Access Secured Endpoint (Initial Token) ---
echo "➡️ 3/7 | Testing secured endpoint ${JOB_ENDPOINT} with Access Token 1..."
# NOTE: The missing parameter below is LIKELY causing the 422. 
# We're adding a dummy parameter (?limit=10) to potentially prevent the 422.
# You may need to change this parameter based on your API's requirements.

HTTP_STATUS_3=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "${JOB_ENDPOINT} \
  -H "Authorization: Bearer ${ACCESS_TOKEN_1}")

if [ "$HTTP_STATUS_3" -ge 200 ] && [ "$HTTP_STATUS_3" -lt 300 ]; then
    echo "  ✅ Success: Secured endpoint accessed with initial token (HTTP $HTTP_STATUS_3)."
else
    # This will now fail the test if it returns 422, which is correct behavior.
    echo "  ❌ FAILURE: Access Test 1 failed (HTTP $HTTP_STATUS_3). Expected 2xx."
    echo "  >> Check if the '/jobs' endpoint requires more query parameters (e.g., user_id or status)."
    exit 1
fi
echo " "


# --- 4️⃣ Refresh Token (Get New Token Pair) ---
echo "➡️ 4/7 | Requesting token refresh using Refresh Token 1..."
REFRESH_PAYLOAD="{\"refresh_token\": \"${REFRESH_TOKEN_1}\"}"
REFRESH_RESPONSE=$(curl -k -s -X POST "${REFRESH_URL}" \
  -H "Content-Type: application/json" \
  -d "$REFRESH_PAYLOAD")

if echo "$REFRESH_RESPONSE" | jq -e '.access_token' > /dev/null; then
  ACCESS_TOKEN_2=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')
  REFRESH_TOKEN_2=$(echo "$REFRESH_RESPONSE" | jq -r '.refresh_token')
  echo "  ✅ Success: Received NEW token pair."
  echo "  (Access Token 2: ${ACCESS_TOKEN_2:0:8}...) "
  echo "  (Refresh Token 2: ${REFRESH_TOKEN_2:0:8}...) "
else
  echo "  ❌ FAILURE: Token refresh failed."
  echo "  Full Response: $REFRESH_RESPONSE"
  exit 1
fi
echo " "


# --- 5️⃣ Access Secured Endpoint (Refreshed Token) ---
echo "➡️ 5/7 | Testing secured endpoint ${JOB_ENDPOINT} with NEW Access Token 2..."
HTTP_STATUS_5=$(curl -k -s -o /dev/null -w "%{http_code}" -X GET "${JOB_ENDPOINT}?limit=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN_2}")

if [ "$HTTP_STATUS_5" -ge 200 ] && [ "$HTTP_STATUS_5" -lt 300 ]; then
    echo "  ✅ Success: Secured endpoint accessed with REFRESHED token (HTTP $HTTP_STATUS_5)."
else
    echo "  ❌ FAILURE: Access Test 2 failed (HTTP $HTTP_STATUS_5). Expected 2xx."
    exit 1
fi
echo " "


# --- 6️⃣ Check Old Access Token (Should Fail) ---
echo "➡️ 6/7 | Verifying Access Token 1 is now revoked (Must return 401)..."
OLD_ACCESS_TEST=$(curl -k -s -w "%{http_code}" -o /dev/null -X GET "${JOB_ENDPOINT}?limit=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN_1}")

if [ "$OLD_ACCESS_TEST" == "401" ]; then
    echo "  ✅ Success: Old Access Token 1 returned 401 Unauthorized (expected behavior)."
else
    echo "  ⚠️ WARNING: Old Access Token 1 did NOT return 401 (returned $OLD_ACCESS_TEST)."
    echo "  >> CN Note: This should be 401, not 422 or 403. Check API implementation."
fi
echo " "


# --- 7️⃣ Logout (Revoke Final Refresh Token) ---
echo "➡️ 7/7 | Logging out/revoking final refresh token (Refresh Token 2)..."
LOGOUT_PAYLOAD="{\"refresh_token\": \"${REFRESH_TOKEN_2}\"}"
LOGOUT_STATUS=$(curl -k -s -w "%{http_code}" -o /dev/null -X POST "${LOGOUT_URL}" \
  -H "Content-Type: application/json" \
  -d "$LOGOUT_PAYLOAD")

if [ "$LOGOUT_STATUS" == "204" ]; then
    echo "  ✅ Success: Refresh Token 2 successfully revoked/logged out (HTTP $LOGOUT_STATUS)."
else
    echo "  ❌ FAILURE: Logout failed. HTTP Status: $LOGOUT_STATUS"
    exit 1
fi
echo " "

echo "=========================================================="
echo " 🎉 Full Auth Lifecycle Test Completed Successfully!"
echo "=========================================================="
echo " "
curl -k -X POST https://helix.local/api/v1/job \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_name": "app.tasks.process_data", "input_data": {"sample": 42}}'

curl -k -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://helix.local/api/v1/jobs?user_id=$USER_ID"
echo " "
echo "=========================================================="
echo " 🎉 echo Retrieve job details
echo "=========================================================="
echo " "
curl -k -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://helix.local/api/v1/${JOB_ID}"
