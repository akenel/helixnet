# src/services/keycloak_service.py
"""
Keycloak Proxy Service
Manages all interactions with Keycloak API

Includes retry logic for startup race conditions (Keycloak may not be ready).
"""

import aiohttp
import asyncio
import logging
from typing import Optional
from fastapi import HTTPException
from pydantic import SecretStr
from src.schemas.user_schema import UserCreate
from src.exceptions.user_exceptions import DuplicateUserError, KeycloakRegistrationFailed

logger = logging.getLogger("🔑 KeycloakProxy")
logger.setLevel(logging.INFO)

# Retry configuration for Keycloak connection
KEYCLOAK_MAX_RETRIES = 5
KEYCLOAK_RETRY_DELAY = 3  # seconds (will use exponential backoff)

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

    async def _wait_for_keycloak(self) -> bool:
        """Wait for Keycloak to be ready with exponential backoff."""
        for attempt in range(KEYCLOAK_MAX_RETRIES):
            try:
                async with self.http_session.get(
                    f"{self.BASE_URL}/realms/master/.well-known/openid-configuration",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Keycloak ready (attempt {attempt + 1})")
                        return True
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                delay = KEYCLOAK_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"⏳ Keycloak not ready (attempt {attempt + 1}/{KEYCLOAK_MAX_RETRIES}), "
                    f"retrying in {delay}s... ({type(e).__name__})"
                )
                await asyncio.sleep(delay)
        logger.error(f"❌ Keycloak not ready after {KEYCLOAK_MAX_RETRIES} attempts")
        return False

    async def _get_admin_token(self) -> str:
        """Get admin token with retry logic for startup race condition."""
        if self._admin_token:
            return self._admin_token

        # Wait for Keycloak to be ready first
        if not await self._wait_for_keycloak():
            raise KeycloakRegistrationFailed("Keycloak not available after retries")

        # Use fallback admin login with retry
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "helix_user",
            "password": "helix_pass",
        }

        last_error = None
        for attempt in range(KEYCLOAK_MAX_RETRIES):
            try:
                async with self.http_session.post(
                    f"{self.BASE_URL}/realms/master/protocol/openid-connect/token",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        token_data = await resp.json()
                        self._admin_token = token_data["access_token"]
                        logger.info("✅ Keycloak admin token acquired")
                        return self._admin_token
                    else:
                        text = await resp.text()
                        last_error = f"HTTP {resp.status}: {text}"
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = f"{type(e).__name__}: {e}"

            if attempt < KEYCLOAK_MAX_RETRIES - 1:
                delay = KEYCLOAK_RETRY_DELAY * (2 ** attempt)
                logger.warning(f"⏳ Token request failed (attempt {attempt + 1}), retrying in {delay}s...")
                await asyncio.sleep(delay)

        raise KeycloakRegistrationFailed(f"Failed to get admin token after {KEYCLOAK_MAX_RETRIES} attempts: {last_error}")

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
