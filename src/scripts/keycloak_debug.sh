#!/bin/bash
#
# Sanity checks for Keycloak API connectivity from within the helix-web-app container.
# This script acquires an admin token, checks the 'kc-realm-dev' realm, and attempts to
# create a test user, confirming the entire authentication flow works.

# --- Configuration (MUST MATCH Keycloak setup) ---
KC_HOST="keycloak:8080"
KC_REALM="master" # Use master realm for admin login (where kc_user exists)
TARGET_REALM="kc-realm-dev" # The realm your application uses
KC_USER="kc_user" # As determined by docker inspect
KC_PASS="kc_pass" # Placeholder: Replace with your actual password

# --- Admin Client Configuration for master realm token acquisition ---
# The standard client for admin access in the 'master' realm is 'admin-cli'.
ADMIN_CLIENT_ID="admin-cli"
TEST_USERNAME="test.user.kc.check"
TEST_USER_PASSWORD="SecureTestPassword123"

echo "====================================================="
echo "🔑 KEYCLOAK SANITY CHECK STARTING"
echo "Targeting internal host: http://${KC_HOST}"
echo "Admin User: ${KC_USER}"
echo "Admin Client ID: ${ADMIN_CLIENT_ID}"
echo "====================================================="

# 1. ACQUIRE ADMIN TOKEN
# =================================================================
echo -e "\n--- 1. ACQUIRING ADMIN TOKEN ---"
TOKEN_RESPONSE=$(curl -s -X POST "http://${KC_HOST}/realms/${KC_REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KC_USER}" \
  -d "password=${KC_PASS}" \
  -d 'grant_type=password' \
  -d "client_id=${ADMIN_CLIENT_ID}" # FIXED: Using the master realm's admin-cli client ID
)

ADMIN_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ FAILURE: Failed to get ADMIN_TOKEN."
  echo "Response Body: $TOKEN_RESPONSE"
  exit 1
fi

echo "✅ SUCCESS: Admin Token acquired."
echo "Token starts with: ${ADMIN_TOKEN:0:20}..."

# 2. SANITY CHECK: LIST REALMS (Secured GET request)
# =================================================================
echo -e "\n--- 2. SANITY CHECK: INSPECTING '${TARGET_REALM}' REALM ---"
REALM_RESPONSE=$(curl -s -X GET "http://${KC_HOST}/admin/realms/${TARGET_REALM}" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
)

if echo "$REALM_RESPONSE" | grep -q "\"realm\":\"${TARGET_REALM}\""; then
  echo "✅ SUCCESS: Realm inspection succeeded. Keycloak is accessible and token is valid."
else
  echo "❌ FAILURE: Could not retrieve realm info with admin token."
  echo "Response Body: $REALM_RESPONSE"
  exit 1
fi

# 3. ADVANCED CHECK: CREATE A TEST USER (Secured POST request)
# =================================================================
echo -e "\n--- 3. ADVANCED CHECK: CREATING TEST USER '${TEST_USERNAME}' ---"

USER_DATA='{
  "username": "'${TEST_USERNAME}'",
  "enabled": true,
  "emailVerified": true,
  "credentials": [
    {
      "type": "password",
      "value": "'${TEST_USER_PASSWORD}'",
      "temporary": false
    }
  ]
}'

CREATE_USER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://${KC_HOST}/admin/realms/${TARGET_REALM}/users" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$USER_DATA"
)

if [ "$CREATE_USER_STATUS" -eq 201 ]; then
  echo "✅ SUCCESS: Test user created (HTTP 201)."
else
  echo "❌ FAILURE: Failed to create test user. HTTP Status: ${CREATE_USER_STATUS}"
  exit 1
fi

# 4. CLEANUP (Delete the test user)
# =================================================================
echo -e "\n--- 4. CLEANUP: DELETING TEST USER ---"
# First, get the user ID
USER_ID_RESPONSE=$(curl -s -X GET "http://${KC_HOST}/admin/realms/${TARGET_REALM}/users?username=${TEST_USERNAME}" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json"
)
USER_ID=$(echo "$USER_ID_RESPONSE" | jq -r '.[0].id')

if [ "$USER_ID" == "null" ] || [ -z "$USER_ID" ]; then
    echo "⚠️ WARNING: Could not find user ID for cleanup. Skipping deletion."
else
    DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "http://${KC_HOST}/admin/realms/${TARGET_REALM}/users/${USER_ID}" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}"
    )

    if [ "$DELETE_STATUS" -eq 204 ]; then
        echo "✅ SUCCESS: Test user deleted (HTTP 204)."
    else
        echo "❌ FAILURE: Failed to delete test user. HTTP Status: ${DELETE_STATUS}"
    fi
fi

echo -e "\n====================================================="
echo "Keycloak Sanity Checks Complete."
echo "====================================================="
