# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Startup Logic) - FIX APPLIED
# ======================================================================
# /home/angel/repos/helixnet/app/services/user_service.py
# Import time/asyncio for delays
import asyncio 
import time
import logging
import uuid
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx 
from pydantic import SecretStr
from uuid import UUID

from app.core.config import get_settings
# 🚨 FIX 1: Removed get_password_hash. Keycloak handles passwords.
from app.db.models import UserModel 
from app.schemas.user_schema import UserCreate, UserUpdate
# 🚨 FIX 2: Imported the Keycloak service and custom exceptions
from app.services.keycloak_proxy_service import KeycloakProxyService
from app.exceptions.user_exceptions import (
    DuplicateUserError, 
    KeycloakRegistrationFailed, 
    UserNotFound
) 

# ================================================================
# ⚙️ CONFIGURATION & LOGGER
# ================================================================
settings = get_settings()
logger = logging.getLogger("🛠️ UserService")
logger.setLevel(logging.INFO)

# ⚠️ WARNING: INTERNAL_KEYCLOAK_HOST is only used for the startup 'seeding' function.
# All router-facing logic uses the KeycloakProxyService which manages its own client.
INTERNAL_KEYCLOAK_HOST = "http://keycloak:8080"


# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Startup Logic)
# ======================================================================
async def get_keycloak_admin_token() -> str | None:
    """Acquires Admin Access Token from Keycloak for bootstrap purposes, with retries."""
    
    MASTER_REALM = "master"
    BOOTSTRAP_CLIENT_ID = "admin-cli"
    MAX_RETRIES = 10  # Maximum number of attempts
    RETRY_DELAY = 5   # Delay in seconds between attempts

    TOKEN_URL = f"{INTERNAL_KEYCLOAK_HOST}/realms/{MASTER_REALM}/protocol/openid-connect/token"
    auth_data = {
        "grant_type": "password",
        "client_id": BOOTSTRAP_CLIENT_ID,
        "username": settings.KEYCLOAK_ADMIN_USER,
        "password": settings.KEYCLOAK_ADMIN_PASSWORD,
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                response = await client.post(
                    TOKEN_URL, 
                    data=auth_data, 
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status() # Raises for 4xx/5xx codes
                token_data = response.json()
                
                logger.info(f"✅ Bootstrap Admin Token acquired successfully on attempt {attempt}.")
                return token_data.get("access_token")
                
        except httpx.HTTPStatusError as e:
            # This handles connection refused (if Keycloak is up but misconfigured)
            # or 401/403 errors (if credentials are bad)
            status_code = e.response.status_code
            logger.warning(
                f"Keycloak token acquisition failed (Status {status_code}) on attempt {attempt}/{MAX_RETRIES}. Retrying in {RETRY_DELAY}s."
            )
        except Exception as e:
            # This handles ConnectionRefusedError or DNS resolution failure (Keycloak not yet ready)
            logger.warning(
                f"Keycloak connection failed on attempt {attempt}/{MAX_RETRIES}. Retrying in {RETRY_DELAY}s. Error: {type(e).__name__}"
            )

        # Wait before the next attempt
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)

    # If the loop completes without success
    logger.error("🚨 Keycloak Admin Token acquisition failed after all attempts. Service is unreachable or credentials are bad.")
    return None#################################################################################
async def create_initial_users(db: AsyncSession) -> None:
    """Creates initial users in the database and in Keycloak."""
    logger.info("🌱 Starting initial user seeding process...")
    
    # NOTE: This seeding function is complex because it bridges two worlds (startup and runtime).
    initial_users_data = [
        {
            "username": settings.HX_SUPER_NAME,
            "email": settings.HX_SUPER_EMAIL,
            "password": settings.HX_SUPER_PASSWORD,
            "fullname": "System Administrator",
            "is_admin": True,
            "roles": ["admin", "super_user"]
        }
    ]
    
    keycloak_proxy = KeycloakProxyService() # Instantiate proxy for seeding
    admin_token = await get_keycloak_admin_token() # Needs a dedicated token for admin API
    
    if not admin_token:
        logger.error("🚨 Cannot proceed with user seeding: Keycloak Admin Token missing.")
        return

    for user_data in initial_users_data:
        username = user_data["username"]
        # 1. Idempotency Check (Check DB first)
        stmt = select(UserModel).where(username == username)
        db_user_result = await db.execute(stmt)
        if db_user_result.scalar_one_or_none():
            logger.info(f"User '{username}' already exists in DB. Skipping creation.")
            continue

        logger.info(f"Attempting to seed new user: {username}...")
        
        try:
            # 2. Create User in Keycloak (using the Admin token directly)
            keycloak_uid = await keycloak_proxy.create_user_admin_api_direct(
                admin_token=admin_token,
                user_data=UserCreate(**user_data), # Use the Pydantic model for clean data
                initial_roles=user_data["roles"]
            )
            
            # 3. Create User in Local DB (No password hash!)
            new_user = UserModel(
                # Use a random UUID for the local DB ID, Keycloak ID is stored in keycloak_id
                id=uuid.uuid4(), 
                email=user_data["email"],
                username=user_data["username"],
                # 🚨 FIX: Passwords are NOT stored/hashed in the local DB when using Keycloak for auth.
                # We set a dummy hash just to satisfy the database constraint if it exists.
                hashed_password="KEYCLOAK_MANAGED_PASSWORD", 
                fullname=user_data["fullname"],
                is_active=True,
                is_admin=user_data["is_admin"],
                keycloak_id=UUID(keycloak_uid), # Crucially link to Keycloak UID
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add(new_user)
            await db.commit()
            logger.info(f"💾 User '{username}' successfully created in DB and linked to Keycloak.")

        except DuplicateUserError:
             logger.warning(f"Seeding failed for '{username}': User already exists in Keycloak. Continuing.")
        except Exception as e:
            logger.error(f"FATAL ERROR during user seeding for '{username}': {e}", exc_info=True)
            await db.rollback()

    logger.info("✅ Initial user seeding process completed.")


# ======================================================================
# 🧑‍💻 ASYNC USER SERVICE (The Class the Router Needs)
# ======================================================================

class AsyncUserService:
    """
    Core service layer for handling all business logic related to the User model.
    """
    
    def __init__(self, db: AsyncSession):
        """Initializes the service with the database session and Keycloak client."""
        self.db = db
        # 🚨 FIX 3: Instantiate the Keycloak Proxy service for use in public methods
        self.keycloak_service = KeycloakProxyService()

    async def create_user_keycloak_db(self, user_data: UserCreate) -> UserModel:
        """
        Handles user registration by creating the user in Keycloak first, 
        then synchronizing the record to the local database.
        
        Raises: DuplicateUserError, KeycloakRegistrationFailed
        """
        # 1. Idempotency Check (Local DB)
        result = await self.db.execute(select(UserModel).where(or_(UserModel.email == user_data.email, UserModel.username == user_data.username)))
        if result.scalar_one_or_none():
            raise DuplicateUserError(detail=f"User with email '{user_data.email}' or username '{user_data.username}' already exists.")

        # 2. Create User in Keycloak (This will raise DuplicateUserError if Keycloak already has it)
        try:
            # This call attempts to create the user in Keycloak and returns the UUID if successful.
            keycloak_uid = await self.keycloak_service.create_user_admin_api(user_data)
        
        except DuplicateUserError as e:
            logger.warning(f"Registration failed: {e.detail}")
            # Re-raise the custom exception for the router to catch
            raise e
        except Exception as e:
            logger.error(f"Keycloak registration failed unexpectedly: {e}", exc_info=True)
            # Catch all network/proxy errors and wrap in a custom exception
            raise KeycloakRegistrationFailed(detail=f"Keycloak service error during registration: {e}")

        # 3. Create User in Local DB
        new_user = UserModel(
            id=uuid.uuid4(),
            email=user_data.email,
            username=user_data.username,
            # 🚨 FIX: Hashed password is a required field but must be a dummy string
            # to indicate external management.
            hashed_password="KEYCLOAK_MANAGED_PASSWORD",
            fullname=user_data.fullname,
            is_active=True,
            is_admin=False,
            keycloak_id=UUID(keycloak_uid), # Store the Keycloak UUID
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.db.add(new_user)
        
        try:
            await self.db.commit()
            await self.db.refresh(new_user)
            logger.info(f"User '{user_data.username}' successfully registered in Keycloak and local DB.")
            return new_user
        except Exception as e:
            # Critical: If DB commit fails, we must try to delete the user from Keycloak 
            # to prevent a half-registered state (Keycloak has user, DB doesn't).
            await self.db.rollback()
            logger.error(f"DB synchronization failed after successful Keycloak creation. Attempting Keycloak rollback.", exc_info=True)
            # Rollback logic for keycloak needed here if the DB fails.
            # self.keycloak_service.delete_user_admin_api(keycloak_uid)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database registration failed. Please try again.")


    async def update_user_profile(self, user_id: UUID, update_data: UserUpdate) -> Optional[UserModel]:
        """
        Updates a user's profile in the local DB. 
        Note: Keycloak updates (password, email) should happen via the Keycloak service.
        """
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        update_data_dict = update_data.model_dump(exclude_unset=True)
        
        # Handle password change separately as it must go to Keycloak
        password_secret = update_data_dict.pop("password", None)
        if password_secret:
            # 🚨 FIX 4: Use Keycloak service to update the password remotely
            logger.info(f"Attempting to update password for Keycloak user: {user.keycloak_id}")
            await self.keycloak_service.update_user_password(
                user_id=str(user.keycloak_id), 
                new_password=password_secret.get_secret_value()
            )
            # Do NOT update local hashed_password field!

        # Update local DB fields
        for key, value in update_data_dict.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """Retrieves a single user by their unique ID."""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        return result.scalars().first()
        
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Retrieves a paginated list of all users."""
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_user(self, user_id: UUID) -> bool:
        """Deletes a user from the database and Keycloak."""
        result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            # 1. Delete from Keycloak
            if user.keycloak_id:
                try:
                    await self.keycloak_service.delete_user_admin_api(str(user.keycloak_id))
                    logger.info(f"User {user_id} successfully deleted from Keycloak.")
                except Exception as e:
                    # Log error but proceed with local deletion
                    logger.error(f"Failed to delete user {user_id} from Keycloak: {e}")

            # 2. Delete from local DB
            await self.db.delete(user)
            await self.db.commit()
            return True
        return False
