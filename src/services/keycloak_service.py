# src/services/keycloak_service.py
import asyncio
import logging
from typing import Optional, Annotated
import aiohttp
import httpx # Used for handling specific admin token acquisition requests
from pydantic import SecretStr
from fastapi import Depends
from src.core.config import settings
from src.exceptions.user_exceptions import (
    DuplicateUserError,
    KeycloakRegistrationFailed,
)
# ================================================================
# ⚙️ CONFIGURATION & LOGGER
# ================================================================
logger = logging.getLogger("🔑 KeycloakProxy")
logger.setLevel(logging.INFO)
# --- Keycloak Endpoints ---
# BASE_URL is now correctly set to http://keycloak:8080
BASE_URL = settings.KEYCLOAK_SERVER_URL 
REALM = settings.KEYCLOAK_REALM
ADMIN_REALM = settings.KEYCLOAK_MASTER_REALM
KEYCLOAK_HELIX_REALM_INTERNAL_URL = settings.KEYCLOAK_HELIX_REALM_INTERNAL_URL
# Token URL for the target realm (used by the new service client)
TOKEN_URL = f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/token"
# Master token URL for the fallback (used by the legacy admin user)
MASTER_TOKEN_URL = f"{BASE_URL}/realms/{ADMIN_REALM}/protocol/openid-connect/token"
USERS_ADMIN_URL = f"{BASE_URL}/admin/realms/{REALM}/users"
# ======================================================================
# 🔑 KEYCLOAK PROXY SERVICE (Handles all external Keycloak communication)
# ======================================================================
async def get_keycloak_proxy() -> aiohttp.ClientSession:
        """Dependency provider that manages the aiohttp ClientSession lifecycle."""
        async with aiohttp.ClientSession() as session:
            yield KeycloakProxyService(settings, session)
##########################################################################################
class KeycloakProxyService:
    """
    Manages all API interactions with Keycloak for administrative tasks
    (e.g., user creation, role management).
    """
    def __init__(self, settings, session: aiohttp.ClientSession):
        self.settings = settings
        self.http_session = session
        self._admin_token: Optional[str] = None
        # Initialize expiry to 0 to force an immediate token acquisition attempt
        self._token_expiry: Optional[float] = 0
##########################################################################################
    async def _get_admin_token(self) -> str:
        """
        Acquires an admin token using the preferred Service Account (client_credentials) flow.
        Falls back to master admin credentials only if the service account fails.
        """
        now = asyncio.get_event_loop().time()

        # Check if current token is valid (with 60-second buffer)
        if self._admin_token and self._token_expiry > now + 60:
            return self._admin_token

        # 1. PRIMARY: Attempt Dedicated Service Account (client_credentials grant)
        # This is the preferred method for S2S communication.
        try:
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.settings.KEYCLOAK_SERVICE_CLIENT_ID,
                # NOTE: KEYCLOAK_SERVICE_CLIENT_SECRET is not a SecretStr in your config, but we keep the call in case it's changed later.
                "client_secret": self.settings.KEYCLOAK_SERVICE_CLIENT_SECRET,
            }
            # Check if secret needs decoding
            if isinstance(auth_data["client_secret"], SecretStr):
                auth_data["client_secret"] = auth_data["client_secret"].get_secret_value()

            logger.info(f"Attempting token acquisition via Service Account (client: {auth_data['client_id']}).")

            # The dedicated client uses the target realm's token endpoint
            async with self.http_session.post(
                TOKEN_URL,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                response.raise_for_status()
                token_data = await response.json()

                self._admin_token = token_data.get("access_token")
                self._token_expiry = now + token_data.get("expires_in", 300)
                logger.info("✅ Service Account token acquired successfully.")
                return self._admin_token

        except Exception as e:
            # Log failure and fall back
            logger.warning(f"Service Account token acquisition failed. Failing over to Master Admin fallback. Error: {e}")

        # 2. FALLBACK: Master Admin (password grant) - Uses the bootstrapping user
        try:
            auth_data = {
                "grant_type": "password",
                "client_id": "admin-cli", # FIX: Use the standard Keycloak administrative client ID
                "username": self.settings.HX_SUPER_NAME, # Use the explicit superuser for master realm login
                "password": self.settings.HX_SUPER_PASSWORD, # Use the explicit superuser password
            }

            logger.info(f"Attempting token acquisition via Master Admin Fallback (user: {auth_data['username']}).")
            
            # Master token acquisition uses the MASTER REALM endpoint
            async with self.http_session.post(
                MASTER_TOKEN_URL,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                response.raise_for_status()
                token_data = await response.json()

                self._admin_token = token_data.get("access_token")
                self._token_expiry = now + token_data.get("expires_in", 300)
                logger.warning("⚠️ Token acquired via Master Admin fallback.")
                return self._admin_token
        except Exception as e:
            logger.error(f"🚨 FATAL: Keycloak token acquisition failed for both Service Account and Master Admin: {e}", exc_info=True)
            # Re-raise the custom exception to halt startup gracefully
            raise KeycloakRegistrationFailed(detail="Could not acquire Keycloak admin token.")
##########################################################################################
    async def _assign_role(self, user_id: str, role_name: str, token: str):
        """
        🧩 Assigns a specific realm-level role (e.g., 'admin') to a user in Keycloak.
        Gracefully handles 'already assigned' or 'role not found' cases.
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # 1️⃣ Get the role details from the realm
            role_url = f"{KEYCLOAK_HELIX_REALM_INTERNAL_URL}/{role_name}"
            async with self.http_session.get(role_url, headers=headers) as role_response:
                if role_response.status == 404:
                    logger.warning(f"⚠️ Role '{role_name}' not found in Keycloak realm.")
                    return
                role_data = await role_response.json()

            # 2️⃣ Assign the role to the user
            assign_url = f"{USERS_ADMIN_URL}/{user_id}/role-mappings/realm"
            async with self.http_session.post(assign_url, json=[role_data], headers=headers) as assign_response:
                if assign_response.status == 204:
                    logger.info(f"🎩 Assigned role '{role_name}' to user ID: {user_id}")
                elif assign_response.status == 409:
                    logger.info(f"♻️ Role '{role_name}' already assigned to user {user_id}")
                else:
                    assign_response.raise_for_status()

        except aiohttp.ClientResponseError as e:
            logger.error(f"🚨 Failed assigning role '{role_name}' to {user_id}: {e.status} - {e.message}")
            raise KeycloakRegistrationFailed(
                detail=f"Failed assigning role '{role_name}' to {user_id}: {e.status} - {e.message}"
            )

        except Exception as e:
            logger.error(f"💥 Unexpected error assigning role '{role_name}' to {user_id}: {e}", exc_info=True)
            raise KeycloakRegistrationFailed(
                detail=f"Unexpected error assigning role '{role_name}' to {user_id}: {e}"
            )
        
        
##########################################################################################
    async def create_user_admin_api(
        self,
        email: str,
        password: SecretStr,
        first_name: str,
        last_name: str,
        is_admin: bool
    ) -> str:
        """
        🧩 Creates a user in Keycloak via the Admin API.
        Returns the Keycloak UUID (string) of the newly created user.

        💡 Handles duplicates, token issues, and role assignment.
        """

        token = await self._get_admin_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        user_payload = {
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "credentials": [
                {
                    "type": "password",
                    "value": password.get_secret_value(),
                    "temporary": False
                }
            ],
        }

        try:
            async with self.http_session.post(USERS_ADMIN_URL, json=user_payload, headers=headers) as response:
                # 🧱 Conflict → User already exists
                if response.status == 409:
                    msg = f"Keycloak: User with email/username '{email}' already exists."
                    logger.warning(f"⚠️ Duplicate user detected: {msg}")
                    raise DuplicateUserError(msg)

                # 🚨 Raise any other HTTP error (401, 403, 500, etc.)
                response.raise_for_status()

                # ✅ Extract user ID from the Location header
                location_header = response.headers.get('Location')
                if location_header:
                    user_id = location_header.split("/")[-1]
                    logger.info(f"✅ Keycloak user '{email}' created successfully, ID: {user_id}")

                    # 🦸 Assign admin role if required
                    if is_admin:
                        await self._assign_role(user_id, "admin", token)
                        logger.info(f"🦸 Role 'admin' assigned to user {email}.")

                    return user_id

                # If no Location header, treat as partial success
                logger.error("🚨 Keycloak user creation succeeded but missing Location header!")
                raise KeycloakRegistrationFailed(
                    f"Keycloak user created but ID could not be retrieved for '{email}'."
                )

        except aiohttp.ClientResponseError as e:
            # 🧩 Specific handling for HTTP response failures
            logger.error(
                f"💥 Keycloak HTTP Error ({e.status}) while creating '{email}': {e.message}"
            )
            raise KeycloakRegistrationFailed(
                f"Keycloak API error {e.status}: {e.message}"
            )

        except DuplicateUserError as e:
            # 🧩 Don’t wrap again — propagate as-is for caller to handle gracefully
            logger.warning(f"🧠 Duplicate user logic triggered: {str(e)}")
            raise

        except Exception as e:
            # 💣 Catch-all fallback
            logger.error(
                f"🚨 Unexpected Keycloak error during registration of '{email}': {e}",
                exc_info=True
            )
            raise KeycloakRegistrationFailed(
                f"Unexpected Keycloak registration error for '{email}': {e}"
            )
# Alias for use in FastAPI dependency injection
KeycloakProxy = Annotated[KeycloakProxyService, Depends(get_keycloak_proxy)]