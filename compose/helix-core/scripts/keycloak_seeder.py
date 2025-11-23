import requests
import json
import os
import time
from urllib.parse import urljoin
# --- Configuration Constants ---
from src.core.config import settings
INTERNAL_KEYCLOAK_HOST = settings.KEYCLOAK_BASE_URL
KEYCLOAK_URL = settings.KEYCLOAK_BASE_URL
MASTER_REALM = settings.KEYCLOAK_REALM
KEYCLOAK_REALM = settings.KEYCLOAK_REALM
KEYCLOAK_ADMIN_PASSWORD = settings.KEYCLOAK_ADMIN_PASSWORD
# Configuration loaded from environment variables (assuming Keycloak env vars are available)
# KEYCLOAK_URL =  http://keycloak:8080
KEYCLOAK_REALM =  "kc-realm-dev"
MASTER_REALM = "master"
ADMIN_CLIENT_ID = "admin-cli"
ADMIN_USERNAME = settings.KEYCLOAK_ADMIN_USER
ADMIN_PASSWORD = KEYCLOAK_ADMIN_PASSWORD

print(f"🔑 Initializing Keycloak Seeder for Realm: {KEYCLOAK_REALM}")

# --- Helper Functions ---

def get_admin_token(realm=MASTER_REALM):
    """
    Acquires an access token for the master realm admin user.
    This token is needed to manage other realms (like 'kc-realm-dev').
    """
    token_url = urljoin(KEYCLOAK_URL, f"/realms/{realm}/protocol/openid-connect/token")
    
    data = {
        "client_id": ADMIN_CLIENT_ID,
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password",
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=5)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not retrieve Admin Token from {token_url}. Is Keycloak running and initialized?")
        print(e)
        return None

def get_target_realm_roles(admin_token):
    """Retrieves all available roles in the target realm ('kc-realm-dev')."""
    realm_roles_url = urljoin(KEYCLOAK_URL, f"/admin/realms/{KEYCLOAK_REALM}/roles")
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    try:
        response = requests.get(realm_roles_url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Maps role names to their ID (required for user role assignment)
        return {role['name']: role['id'] for role in response.json()}
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not retrieve roles for realm {KEYCLOAK_REALM}. Is the realm imported?")
        print(e)
        return {}


def create_user(admin_token, user_data, role_ids, role_map):
    """Creates a user and assigns roles."""
    user_url = urljoin(KEYCLOAK_URL, f"/admin/realms/{KEYCLOAK_REALM}/users")
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # 1. Create the user
    user_payload = {
        "username": user_data['email'],
        "email": user_data['email'],
        "firstName": user_data['first_name'],
        "lastName": user_data['last_name'],
        "enabled": True,
        "emailVerified": True,
        "credentials": [
            {
                "type": "password",
                "value": user_data['password'],
                "temporary": False
            }
        ]
    }
    
    try:
        response = requests.post(user_url, headers=headers, json=user_payload, timeout=5)
        if response.status_code == 409:
            print(f"  👉 User already exists: {user_data['email']}. Skipping creation.")
            return

        response.raise_for_status()
        print(f"  ✅ Created user: {user_data['email']}")
        
        # 2. Get the new user's ID
        # Keycloak doesn't return the ID on creation, so we have to search
        search_response = requests.get(f"{user_url}?username={user_data['email']}", headers=headers, timeout=5)
        search_response.raise_for_status()
        user_id = search_response.json()[0]['id']

        # 3. Assign roles
        roles_to_assign = [{"id": role_map.get(role_id)} for role_id in role_ids if role_map.get(role_id)]
        if roles_to_assign:
            role_assignment_url = f"{user_url}/{user_id}/role-mappings/realm"
            role_response = requests.post(role_assignment_url, headers=headers, json=roles_to_assign, timeout=5)
            role_response.raise_for_status()
            print(f"  ✅ Assigned roles {role_ids} to {user_data['email']}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR processing user {user_data['email']}: {e}")

# --- Main Execution ---

# Define the initial users and their roles in the 'kc-realm-dev' realm
INITIAL_USERS = [
    {
        "email": "chuck.norris@helix.net", 
        "first_name": "Chuck", 
        "last_name": "Norris", 
        "password": "Chuck", 
        "roles": ["admin", "user"] # Has full access
    },
    {
        "email": "bruce.lee@helix.net", 
        "first_name": "Bruce", 
        "last_name": "Lee", 
        "password": "Bruce", 
        "roles": ["user"] # Standard user
    },
    {
        "email": "angel.dev@helix.net", 
        "first_name": "Angel", 
        "last_name": "Dev", 
        "password": "Angel", 
        "roles": ["user"] # Dev/Tester account
    },
]

# We need to wait for Keycloak to be up and the 'kc-realm-dev' realm to be imported
print("⏳ Waiting for Keycloak service and realm import to complete (up to 30 seconds)...")
time.sleep(15) # Give keycloak service time to settle

admin_access_token = get_admin_token()

if admin_access_token:
    print("🔑 Master Admin Token acquired.")
    
    # Get the role IDs for the target realm
    realm_role_map = get_target_realm_roles(admin_access_token)
    
    if realm_role_map:
        print(f"✅ Found roles: {list(realm_role_map.keys())}")
        
        print(f"\n🚀 Seeding {len(INITIAL_USERS)} users into the {KEYCLOAK_REALM} realm...")
        for user in INITIAL_USERS:
            create_user(admin_access_token, user, user['roles'], realm_role_map)
        
        print("\n✨ Keycloak Seeding Complete! The users are ready for login.")
    else:
        print("🛑 Cannot proceed: Could not retrieve roles. Keycloak setup is incomplete.")

else:
    print("🛑 Cannot proceed: Failed to get Master Admin Token.")
    
