import asyncio
import logging
from typing import Optional, List
from datetime import datetime, UTC
from uuid import UUID
import aiohttp
import httpx # Used internally for seeding token acquisition
from pydantic import SecretStr

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import UserModel
# REMOVED: from src.routes.users_router import UserService 
# Rationale: This import caused the circular dependency because users_router 
# needs AsyncUserService from this file.

from src.schemas.user_schema import UserCreate, UserRead, UserUpdate
from src.services.keycloak_service import KeycloakProxyService
from src.exceptions.user_exceptions import (
    DuplicateUserError,
    KeycloakRegistrationFailed,
)
# ADDED: This import is necessary for the `get_password_hash` call in `create_initial_users`.
import src.core.local_auth_service as local_auth_service 

# ================================================================
# ⚙️ CONFIGURATION & LOGGER
# ================================================================
logger = logging.getLogger("🌱 UserService")
logger.setLevel(logging.INFO)
# --- Configuration Constants ---
INTERNAL_KEYCLOAK_HOST = settings.KEYCLOAK_SERVER_URL
MASTER_REALM = settings.KEYCLOAK_MASTER_REALM
# ======================================================================
# 🧑‍💻 ASYNC USER SERVICE (The Class the Router Needs)
# ======================================================================
class AsyncUserService:
    # Assuming 'keycloak_proxy' is injected into the service class
    def __init__(self, keycloak_proxy: KeycloakProxyService, db_session: AsyncSession):
        self.keycloak_proxy = keycloak_proxy
        self.db = db_session
        # ... other initializations

    # 🚨 This is the function the router is calling, so it MUST exist.
    async def register_new_user(self, user_data: UserCreate) -> UserRead:
        """
        1. Creates the user in Keycloak (using the powerful admin API).
        2. Saves the Keycloak-assigned UUID and user data to the local database (DB).
        """
        
        # 1. Create the user in Keycloak using your complex logic
        # We assume the KeycloakProxyService has the 'create_user_admin_api' method
        keycloak_user_id = await self.keycloak_proxy.create_user_admin_api(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_admin=False # Default to non-admin upon registration
        )

        # 2. Save the user record to your local PostgreSQL DB
        # You need to implement your ORM/database logic here, using the keycloak_user_id
        # as the primary ID (e.g., ORM_User(id=keycloak_user_id, ...))
        
        # NOTE: The actual DB insertion and ORM mapping logic is not shown here,
        # but you must save the user ID returned from Keycloak!
        # new_db_user = await self._create_db_user(keycloak_user_id, user_data)
        
        # 3. Return the Pydantic read model
        # return UserRead.model_validate(new_db_user)
        
        # Temporary placeholder return to ensure the function signature is correct:
        return UserRead(
            id=keycloak_user_id,
            email=user_data.email,
            username=user_data.username,
            is_active=True,
            is_superuser=False,
            created_at=datetime.now()
        )
    
    # 🦸 The specific Keycloak Admin API interaction logic (already provided by you)
    # If this method is on the Keycloak Proxy service, it should be called via self.keycloak_proxy
    # If it's intended to be part of the AsyncUserService, you would move it here.
    # Given the name, it belongs in a dedicated Keycloak Proxy/Client class.
    
    # For clarity, ensure your Keycloak Proxy class (KeycloakProxyService) 
    # contains the `create_user_admin_api` function exactly as you wrote it
# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Startup Logic)
# ======================================================================


async def get_keycloak_admin_token() -> str | None:
    """
    Acquires Admin Access Token from Keycloak for bootstrap purposes, with retries.
    Uses httpx for simplicity during startup, separate from the main service's aiohttp.
    """
    BOOTSTRAP_CLIENT_ID = "admin-cli"
    MAX_RETRIES = 10
    RETRY_DELAY = 5
    KC_ADM = settings.HX_SUPER_NAME
    KC_PASS = settings.HX_SUPER_PASSWORD # This is assumed to be a plain string here or converted before use.

    TOKEN_URL = f"{INTERNAL_KEYCLOAK_HOST}/realms/{MASTER_REALM}/protocol/openid-connect/token"
    auth_data = {
        "grant_type": "password",
        "client_id": BOOTSTRAP_CLIENT_ID,
        "username": KC_ADM,
        "password": KC_PASS,
    }

    logger.info("💥 [DEBUG START] Entering Bootstrap Token Acquisition.")
    logger.info(f"🔑 [DEBUG URL] Target Master Token URL: {TOKEN_URL}")
    logger.info(f"🔑 [DEBUG PAYLOAD] Client ID: {BOOTSTRAP_CLIENT_ID} | Username: {KC_ADM}")


    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Using httpx for seeding token acquisition
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                response = await client.post(
                    TOKEN_URL,
                    data=auth_data, # Use full auth_data for network POST
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status() # Raises for 4xx/5xx codes
                token_data = response.json()
                logger.info(f"✅ [SUCCESS] Bootstrap Admin Token acquired successfully on attempt {attempt}.")
                return token_data.get("access_token")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text
            logger.error(
                f"❌ [401 FAILED KICKiS] Status {status_code} on attempt {attempt}. "
                f"Keycloak Error Body: {response_text}. Retrying in {RETRY_DELAY}s."
            )
        except Exception as e:
            # Catch network/connection errors (Keycloak not yet ready)
            logger.warning(
                f"⚠️ [CONNECTION FAIL] Keycloak network error on attempt {attempt}/{MAX_RETRIES}. "
                f"Error Type: {type(e).__name__}. Retrying in {RETRY_DELAY}s."
            )
        # Wait before the next attempt
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)

    # If the loop completes without success
    logger.critical("🚨 KEYCLOAK HALT: Admin Token acquisition failed after all attempts. Check MASTER_REALM credentials/client configuration match both realms.")
    return None

async def create_initial_users(db: AsyncSession) -> None:
    """
    Creates initial users in the database and in Keycloak, with verbose logging.
    """
    logger.info("🌱 [SEEDER START] Initial Keycloak ADMIN user seeding process initiated.")
    initial_users_data = [
        {
            "username": "taxman",
            "email": "taxman@helix.net",
            "password": "taxman", # This password will be hashed/stored by Keycloak/local_auth
            "fullname": "taxman",
            "is_admin": True,
            "roles": ["guest", "auditor"]
        }
    ]

    logger.info("🔑 [KEYCLOAK] Attempting to acquire bootstrap admin token...")
    admin_token = await get_keycloak_admin_token()

    if not admin_token:
        logger.error("🚨 [HALT] Cannot proceed with user seeding: Keycloak Admin Token missing.")
        return

    # NOTE: To use the KeycloakProxyService, we need an aiohttp session.
    # Since this is a startup function, we create a temporary one here.
    async with aiohttp.ClientSession() as http_session:
        keycloak_service = KeycloakProxyService(settings=settings, session=http_session)

        for user_data in initial_users_data:
            username = user_data["username"]

            # 1. Idempotency Check (Check DB first)
            logger.info(f"🔎 [DB CHECK] Checking local database for existing user: '{username}'...")
            stmt = select(UserModel).where(UserModel.username == username)
            db_user_result = await db.execute(stmt)

            if db_user_result.scalar_one_or_none():
                logger.info(f"⏭️ [SKIP] User '{username}' already exists in DB. Skipping creation step.")
                continue

            logger.info(f"🎯 [NEW USER] Starting full creation flow for user: {username}...")
            
            # Use SecretStr for the password before passing to Keycloak service
            password_secret = SecretStr(user_data["password"])

            try:
                # Assuming KeycloakProxyService handles user creation and role assignment
                keycloak_uuid = await keycloak_service.create_user_admin_api(
                    email=user_data["email"],
                    password=password_secret,
                    first_name=user_data["fullname"].split()[0], # Simple parsing
                    last_name=user_data["fullname"].split()[-1],
                    is_admin=user_data["is_admin"]
                )

                # 2. Create the user in the local database (sync with Keycloak UUID)
                new_db_user = UserModel(
                    id=keycloak_uuid, # Use Keycloak ID as local primary key
                    username=username,
                    email=user_data["email"],
                    # Use the imported local_auth_service
                    hashed_password=local_auth_service.get_password_hash(user_data["password"]), 
                    is_active=True,
                    is_admin=user_data["is_admin"],
                )
                db.add(new_db_user)
                await db.commit()
                logger.info(f"✅ User '{username}' created locally and synchronized with Keycloak ID: {keycloak_uuid}.")

            except DuplicateUserError:
                 logger.warning(f"⚠️ [IDEMPOTENCY] Seeding skipped for '{username}': User already exists in Keycloak.")
            except Exception as e:
                logger.error(f"💣 [FATAL ERROR] Failed to seed user '{username}'. Rolling back DB transaction.", exc_info=True)
                await db.rollback()
                raise e

    logger.info("🏁 [SEEDER END] Initial user seeding process completed.")