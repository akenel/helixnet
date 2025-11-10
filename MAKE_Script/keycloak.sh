#!/usr/bin/env bash
#
# Keycloak Management Script
# Purpose: Acquires an admin token and performs user/role management via the Keycloak REST API.
#
set -euo pipefail

# --- ARGUMENT DEFINITION (Expected order for all commands) ---
ACTION="$1" # The command verb (e.g., 'create-user', 'list-roles')
WEB_SERVICE="$2"
KC_HOST="$3"
KC_REALM="$4"
KC_CLIENT_ID="$5"
KC_CLIENT_SECRET="$6"
USERNAME="${7:-}"       # Optional: Default to empty string
ROLE="${8:-}"           # Optional: Default to empty string
FIRST_NAME="${9:-}"     # Optional: Default to empty string
LAST_NAME="${10:-}"     # Optional: Default to empty string

# --- 1. Token Acquisition Function ---
# This function uses $2-$6 (WEB_SERVICE, KC_HOST, KC_REALM, KC_CLIENT_ID, KC_CLIENT_SECRET)
get_admin_token() {
    local token_response
    local admin_token
    echo "🔑 Acquiring admin token for realm: $KC_REALM"
    
    # Use $2-$6 variables defined above
    token_response=$(docker exec -i "$WEB_SERVICE" curl -s -X POST \
      "$KC_HOST/realms/$KC_REALM/protocol/openid-connect/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "grant_type=client_credentials" \
      -d "client_id=$KC_CLIENT_ID" \
      -d "client_secret=$KC_CLIENT_SECRET")

    admin_token=$(echo "$token_response" | jq -r '.access_token')
    
    if [[ -z "$admin_token" || "$admin_token" == "null" ]]; then
      echo "❌ Failed to get admin token. Response:"
      echo "$token_response"
      exit 1
    fi
    
    echo "$admin_token"
}

ADMIN_TOKEN=$(get_admin_token)

# --- 2. Action Logic ---
case "$ACTION" in

  create-user)
    # Check for required user arguments (index 7-10)
    if [[ -z "$USERNAME" || -z "$ROLE" || -z "$FIRST_NAME" || -z "$LAST_NAME" ]]; then
        echo "❌ Command 'create-user' requires USERNAME, ROLE, FIRST_NAME, and LAST_NAME."
        exit 1
    fi
    
    USER_PASS="${USERNAME}_pass"
    USER_JSON=$(jq -n \
      --arg username "$USERNAME" \
      --arg email "${USERNAME}@${LAST_NAME}.net" \
      --arg first "$FIRST_NAME" \
      --arg last "$LAST_NAME" \
      --arg password "$USER_PASS" \
      '{username: $username, email: $email, firstName: $first, lastName: $last, enabled: true,
        credentials: [{type: "password", value: $password, temporary: false}] }')

    KC_USERS_URL="$KC_HOST/admin/realms/$KC_REALM/users"
    
    # 1. Create User
    echo "👤 Attempting to create user $USERNAME..."
    RESPONSE=$(docker exec -i "$WEB_SERVICE" curl -s -o /dev/null -w "%{http_code}" -X POST \
      "$KC_USERS_URL" -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$USER_JSON")

    if [[ "$RESPONSE" == "201" ]]; then
      echo "✅ User created successfully. Initial Password: $USER_PASS"
    elif [[ "$RESPONSE" == "409" ]]; then
      echo "⚠️ User already exists. Proceeding with role assignment..."
    else
      echo "❌ User creation failed. HTTP $RESPONSE"
      exit 1
    fi

    # 2. Get User ID
    USER_ID=$(docker exec -i "$WEB_SERVICE" curl -s -X GET \
      "$KC_USERS_URL?username=$USERNAME" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

    if [[ -z "$USER_ID" || "$USER_ID" == "null" ]]; then
      echo "❌ Could not retrieve user ID for $USERNAME."
      exit 1
    fi

    # 3. Get Role ID
    ROLE_DATA=$(docker exec -i "$WEB_SERVICE" curl -s -X GET \
      "$KC_HOST/admin/realms/$KC_REALM/roles/$ROLE" \
      -H "Authorization: Bearer $ADMIN_TOKEN")

    ROLE_ID=$(echo "$ROLE_DATA" | jq -r '.id')

    if [[ -z "$ROLE_ID" || "$ROLE_ID" == "null" ]]; then
      echo "❌ Role '$ROLE' not found in realm."
      exit 1
    fi

    # 4. Assign Role
    ROLE_PAYLOAD=$(jq -n --arg id "$ROLE_ID" --arg name "$ROLE" '[{id: $id, name: $name}]')
    docker exec -i "$WEB_SERVICE" curl -s -o /dev/null -w "%{http_code}" -X POST \
      "$KC_HOST/admin/realms/$KC_REALM/users/$USER_ID/role-mappings/realm" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$ROLE_PAYLOAD"

    echo "✅ Role '$ROLE' assigned to user '$USERNAME'."
    ;;

  list-roles)
    echo "🧾 Listing all realm roles..."
    ROLE_LIST=$(docker exec -i "$WEB_SERVICE" curl -s -X GET \
      "$KC_HOST/admin/realms/$KC_REALM/roles" \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[].name')
    
    if [[ -z "$ROLE_LIST" ]]; then
        echo "❌ No roles found or API call failed."
    else
        echo -e "--- Roles in $KC_REALM ---"
        echo "$ROLE_LIST"
        echo "--------------------------"
    fi
    ;;

  *)
    echo "Usage: ./keycloak.sh <command> <keycloak_args...>"
    echo "Commands: create-user, list-roles"
    exit 1
    ;;
esac
# --- End of Script ---