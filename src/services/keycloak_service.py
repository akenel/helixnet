# src/services/keycloak_service.py
"""
Keycloak Proxy Service
Manages all interactions with Keycloak API
"""

import aiohttp
import logging
from typing import Optional
from fastapi import HTTPException
from pydantic import SecretStr
from src.schemas.user_schema import UserCreate
from src.exceptions.user_exceptions import DuplicateUserError, KeycloakRegistrationFailed

logger = logging.getLogger("🔑 KeycloakProxy")
logger.setLevel(logging.INFO)

class KeycloakProxyService:
    """Async Keycloak API integration."""

    def __init__(self, settings, session: aiohttp.ClientSession):
        self.settings = settings
        self.http_session = session
        self._admin_token: Optional[str] = None

        # For now hardcode endpoints
        self.BASE_URL = "http://keycloak:8080"
        self.REALM = "master"
        self.USERS_ADMIN_URL = f"{self.BASE_URL}/admin/realms/{self.REALM}/users"

    async def _get_admin_token(self) -> str:
        if self._admin_token:
            return self._admin_token
        # Use fallback admin login
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "helix_user",
            "password": "helix_pass",
        }
        async with self.http_session.post(
            f"{self.BASE_URL}/realms/master/protocol/openid-connect/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise KeycloakRegistrationFailed(f"Failed to get admin token: {text}")
            token_data = await resp.json()
            self._admin_token = token_data["access_token"]
            return self._admin_token

    async def register_user(self, user: UserCreate) -> dict:
        """Register user in Keycloak."""
        token = await self._get_admin_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "username": user.username,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "enabled": True,
            "credentials": [{"type": "password", "value": user.password, "temporary": False}],
        }
        async with self.http_session.post(self.USERS_ADMIN_URL, json=payload, headers=headers) as resp:
            if resp.status == 409:
                raise DuplicateUserError(f"User '{user.email}' exists in Keycloak.")
            if resp.status not in (200, 201, 204):
                text = await resp.text()
                raise KeycloakRegistrationFailed(f"Keycloak API error: {text}")
            user_id = resp.headers.get("Location", "").split("/")[-1]
            logger.info(f"✅ Keycloak user created: {user.username} ID={user_id}")
            return {"id": user_id, "email": user.email}

# Dependency injection
async def get_keycloak_proxy():
    import aiohttp
    async with aiohttp.ClientSession() as session:
        yield KeycloakProxyService(settings=None, session=session)
