import requests
import os
import sys
import json
import time

# --- Keycloak Configuration (Using environment variables set in docker-compose) ---
# The internal service name and port are used for container-to-container communication.
# FIX: Construct BASE_URL from defined ENV variables (KC_HOST, KC_HTTP_PORT)
KC_HOSTNAME = os.environ.get('KC_HOSTNAME', 'keycloak')
KC_HTTP_PORT = os.environ.get('KC_HTTP_PORT', '8080')
KEYCLOAK_BASE_URL = f"{KC_HOSTNAME}:{KC_HTTP_PORT}"

# FIX: The Admin/Bootstrap token MUST be retrieved from the stable 'master' realm
# using the 'admin-cli' client and the main admin credentials during initial setup.
KC_REALM = "master" 

KC_CLIENT_ID = "admin-cli"
KC_USERNAME = os.environ.get('KEYCLOAK_ADMIN', 'helix_user') 
KC_PASSWORD = os.environ.get('KEYCLOAK_ADMIN_PASSWORD', 'helix_pass') 

TOKEN_URL = f"{KEYCLOAK_BASE_URL}/realms/{KC_REALM}/protocol/openid-connect/token"

def get_admin_token(max_retries=10, delay=5):
    """
    Acquires the Keycloak Admin Token from the 'master' realm.
    Retries on connection errors (Keycloak not ready).
    """
    print("---------------------------------------------------------")
    print(f"🔑 Requesting Admin Token from: {TOKEN_URL}")
    print(f"👤 Using User: {KC_USERNAME} (Client: {KC_CLIENT_ID})")
    print("---------------------------------------------------------")

    for attempt in range(max_retries):
        try:
            payload = {
                'grant_type': 'password',
                'client_id': KC_CLIENT_ID,
                'username': KC_USERNAME,
                'password': KC_PASSWORD,
            }

            response = requests.post(TOKEN_URL, data=payload, timeout=10)
            
            # Check for 401 Unauthorized (likely wrong credentials or realm)
            if response.status_code == 401:
                print(f"❌ Keycloak Admin Token acquisition failed: Client error '401 Unauthorized'.")
                print("   Check KEYCLOAK_ADMIN/KEYCLOAK_ADMIN_PASSWORD in your .env and ensure the token URL is correct.")
                # We exit here because the credentials or realm are fundamentally wrong
                sys.exit(1)

            response.raise_for_status() # Raises HTTPError for 4xx/5xx status codes

            data = response.json()
            token = data.get('access_token')
            
            if token:
                print("✅ TOKEN ACQUIRED SUCCESSFULLY!")
                print(f"   Realm: {KC_REALM} (Auth for bootstrap admin)")
                print(f"   Token Type: {data.get('token_type')}")
                print(f"   Expires In: {data.get('expires_in')} seconds")
                
                # Simple decode to show the payload (not strictly necessary but useful for debugging)
                try:
                    import base64
                    
                    # Split the JWT into header, payload, and signature
                    _, payload_base64, _ = token.split('.')
                    # Base64 decode and convert to dictionary
                    # Padding might be required for base64url to standard base64
                    padding = len(payload_base64) % 4
                    if padding == 2:
                        payload_base64 += '=='
                    elif padding == 3:
                        payload_base64 += '='
                        
                    decoded_payload = base64.urlsafe_b64decode(payload_base64.encode('utf-8')).decode('utf-8')
                    payload_data = json.loads(decoded_payload)
                    
                    print("\n--- DECODED TOKEN PAYLOAD (THE PROOF) ---")
                    print(json.dumps(payload_data, indent=2))
                    print("-----------------------------------------")
                    
                except Exception:
                    # If decoding fails, just print the raw token
                    print(f"\n--- RAW TOKEN (Cannot decode) ---")
                    print(token)
                    print("---------------------------------")


                return token
            else:
                print("❌ Token acquired, but 'access_token' field missing in response.")
                sys.exit(1)
        
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Keycloak connection failed (Attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ Keycloak connection failed after {max_retries} attempts. Error: {e}")
                print("   Ensure the 'keycloak' service is running and healthy.")
                sys.exit(1)
        
    return None

if __name__ == "__main__":
    admin_token = get_admin_token()
    if admin_token:
        sys.exit(0)
    else:
        sys.exit(1)
