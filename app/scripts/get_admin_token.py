import os
import requests
import json
import base64
from urllib.parse import urljoin

# --- Configuration (Read from container environment) ---
KC_HOST = os.environ.get("KC_HOST", "keycloak")
KC_HTTP_PORT = os.environ.get("KC_HTTP_PORT", "8080")
ADMIN_USERNAME = os.environ.get("KC_BOOTSTRAP_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("KC_BOOTSTRAP_ADMIN_PASSWORD", "admin")
CLIENT_ID = "admin-cli"  # Standard Keycloak client for master realm admin access

# We use the master realm for the bootstrap admin user
TOKEN_URL = f"http://{KC_HOST}:{KC_HTTP_PORT}/realms/master/protocol/openid-connect/token"


def decode_jwt_payload(jwt_token):
    """Decodes the payload section of a JWT."""
    try:
        # JWT format is header.payload.signature
        _, payload, _ = jwt_token.split('.')
        # Pad payload with '=' if necessary (standard base64 requirement)
        padding = len(payload) % 4
        if padding > 0:
            payload += '=' * (4 - padding)
        
        # Decode and load the JSON payload
        decoded_bytes = base64.b64decode(payload)
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception as e:
        return {"error": "Failed to decode JWT payload", "details": str(e)}

def get_admin_token():
    """Requests an admin access token from the Keycloak master realm."""
    
    print("\n---------------------------------------------------------")
    print(f"🔑 Requesting Admin Token from: {TOKEN_URL}")
    print(f"👤 Using User: {ADMIN_USERNAME} (Client: {CLIENT_ID})")
    print("---------------------------------------------------------")

    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
    }

    try:
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        access_token = data.get("access_token")

        if not access_token:
            print("❌ ERROR: Keycloak did not return an access_token.")
            print(f"Response: {data}")
            return
        
        # Decode and print the token details
        token_payload = decode_jwt_payload(access_token)
        
        print("✅ TOKEN ACQUIRED SUCCESSFULLY!")
        print(f"   Realm: master (Auth for bootstrap admin)")
        print(f"   Token Type: {data.get('token_type')}")
        print(f"   Expires In: {data.get('expires_in')} seconds")
        print("\n--- DECODED TOKEN PAYLOAD (THE PROOF) ---")
        
        # Pretty print the decoded JWT body
        print(json.dumps(token_payload, indent=2))
        print("-----------------------------------------")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FATAL ERROR: Could not connect to Keycloak.")
        print(f"   Check that the 'keycloak' container is running on {KC_HOST}:{KC_HTTP_PORT}.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    get_admin_token()
