"""
Keycloak Health Check Service
Connects to Keycloak and reports realm status at startup.
"""
import logging
import httpx
from typing import Dict, List, Optional
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_admin_token() -> Optional[str]:
    """
    Get admin access token from Keycloak master realm.
    Uses master realm admin credentials.
    """
    try:
        # Keycloak master realm token endpoint
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_MASTER_REALM}/protocol/openid-connect/token"

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": "admin-cli",
                    "username": settings.HX_SUPER_NAME,
                    "password": settings.HX_SUPER_PASSWORD,
                    "grant_type": "password"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                logger.error(f"Failed to get admin token: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        logger.error(f"Error getting admin token: {e}")
        return None


async def get_realm_info(admin_token: str, realm_name: str) -> Optional[Dict]:
    """
    Get detailed information about a specific realm.
    Returns user count and client count.
    """
    try:
        base_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{realm_name}"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            # Get users count
            users_response = await client.get(
                f"{base_url}/users/count",
                headers=headers,
                timeout=5.0
            )
            user_count = users_response.json() if users_response.status_code == 200 else 0

            # Get clients
            clients_response = await client.get(
                f"{base_url}/clients",
                headers=headers,
                timeout=5.0
            )
            client_count = len(clients_response.json()) if clients_response.status_code == 200 else 0

            return {
                "realm": realm_name,
                "users": user_count,
                "clients": client_count
            }

    except Exception as e:
        logger.warning(f"Error getting info for realm '{realm_name}': {e}")
        return {
            "realm": realm_name,
            "users": "?",
            "clients": "?"
        }


async def check_keycloak_realms() -> Dict[str, any]:
    """
    Check Keycloak connection and report all realms with user/client counts.

    Returns:
        Dict with realm information or error status
    """
    logger.info("🔐 Checking Keycloak realm status...")

    try:
        # Step 1: Get admin token
        admin_token = await get_admin_token()
        if not admin_token:
            logger.error("❌ Failed to authenticate with Keycloak master realm")
            return {
                "status": "error",
                "message": "Failed to authenticate with Keycloak",
                "realms": []
            }

        logger.info("✅ Successfully authenticated with Keycloak master realm")

        # Step 2: Get list of realms
        realms_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(realms_url, headers=headers, timeout=10.0)

            if response.status_code != 200:
                logger.error(f"Failed to fetch realms: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"Failed to fetch realms: {response.status_code}",
                    "realms": []
                }

            realms_list = response.json()
            realm_names = [r["realm"] for r in realms_list]

            logger.info(f"📊 Found {len(realm_names)} realm(s): {', '.join(realm_names)}")

            # Step 3: Get detailed info for each realm
            realm_details = []
            for realm_name in realm_names:
                info = await get_realm_info(admin_token, realm_name)
                realm_details.append(info)

            # Step 4: Print summary table
            print_realm_table(realm_details)

            return {
                "status": "success",
                "realm_count": len(realm_details),
                "realms": realm_details
            }

    except httpx.ConnectError:
        logger.error("❌ Cannot connect to Keycloak - service may not be ready yet")
        return {
            "status": "error",
            "message": "Cannot connect to Keycloak",
            "realms": []
        }
    except Exception as e:
        logger.error(f"❌ Keycloak health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "realms": []
        }


def print_realm_table(realms: List[Dict]):
    """
    Print a formatted table of realm information.
    """
    if not realms:
        logger.warning("⚠️ No realms found!")
        return

    # Table header
    print("\n" + "=" * 70)
    print("🔐 KEYCLOAK REALM STATUS")
    print("=" * 70)
    print(f"{'Realm Name':<35} {'Users':<15} {'Clients':<15}")
    print("-" * 70)

    # Table rows
    for realm in realms:
        realm_name = realm.get("realm", "Unknown")
        users = realm.get("users", "?")
        clients = realm.get("clients", "?")

        # Add emoji indicators
        if realm_name == "master":
            realm_display = f"👑 {realm_name}"
        elif "pos" in realm_name.lower():
            realm_display = f"🛒 {realm_name}"
        elif "dev" in realm_name.lower():
            realm_display = f"💦 {realm_name}"
        else:
            realm_display = f"🔐 {realm_name}"

        print(f"{realm_display:<35} {users:<15} {clients:<15}")

    print("=" * 70)
    print(f"Total Realms: {len(realms)}")
    print("=" * 70 + "\n")

    logger.info(f"✅ Keycloak health check completed - {len(realms)} realm(s) active")


async def verify_pos_users_exist() -> bool:
    """
    Optional: Verify that key POS users exist in the POS realm.
    Returns True if users are found, False otherwise.
    """
    try:
        admin_token = await get_admin_token()
        if not admin_token:
            return False

        # Check for POS realm
        pos_realm = "kc-pos-realm-dev"
        users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{pos_realm}/users"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            # Search for key users
            key_users = ["pam", "felix", "michael", "ralph"]
            found_users = []

            for username in key_users:
                response = await client.get(
                    f"{users_url}?username={username}&exact=true",
                    headers=headers,
                    timeout=5.0
                )

                if response.status_code == 200:
                    users = response.json()
                    if users:
                        found_users.append(username)

            logger.info(f"✅ POS realm key users found: {', '.join(found_users)}")
            return len(found_users) >= 4  # All 4 key users should exist

    except Exception as e:
        logger.warning(f"Could not verify POS users: {e}")
        return False
