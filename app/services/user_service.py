import logging
import uuid
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx 
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.models import User 
from app.schemas.user_schema import UserCreate, UserUpdate

# ================================================================
# ⚙️ CONFIGURATION & LOGGER
# ================================================================
settings = get_settings()
# Use a specific logger name for better log filtering
logger = logging.getLogger("🛠️ UserService")
logger.setLevel(logging.INFO)

# ⚠️ CRITICAL NETWORK FIX: Use the Docker service name for internal calls.
INTERNAL_KEYCLOAK_HOST = "http://keycloak:8080"


# ================================================================
# 🐘 KEYCLOAK ADMIN API HELPERS
# ================================================================

async def get_keycloak_admin_token() -> str | None:
    """
    Acquires an Admin Access Token from Keycloak using client credentials 
    for the admin client. Uses the internal Docker service name 'keycloak'.
    """
    TOKEN_URL = f"{INTERNAL_KEYCLOAK_HOST}/realms/{settings.KC_REALM}/protocol/openid-connect/token"
    
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": settings.KC_CLIENT_ID,
        "client_secret": settings.KC_CLIENT_SECRET,
        "scope": "openid",
    }
    
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                TOKEN_URL, data=auth_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            logger.info("✅ Keycloak Admin Token acquired successfully.")
            return token_data.get("access_token")
    except httpx.RequestError as e:
        logger.error(f"Keycloak Admin Token acquisition failed (Network/Request): {e}", exc_info=False)
    except Exception as e:
        logger.error(f"Keycloak Admin Token acquisition failed (Unknown): {e}", exc_info=True)
    return None

async def create_keycloak_user(admin_token: str, user_data: Dict[str, Any], initial_roles: List[str]) -> str:
    """Creates a user in Keycloak and returns the Keycloak UID."""
    USERS_URL = f"{INTERNAL_KEYCLOAK_HOST}/admin/realms/{settings.KC_REALM}/users"
    
    # 1. Check if user already exists by email/username (optional, but good practice)
    # Keycloak Admin API has a search endpoint, but for simplicity, we rely on the DB check first.

    # 2. Keycloak user creation payload
    kc_payload = {
        "enabled": True,
        "username": user_data["username"],
        "email": user_data["email"],
        "firstName": user_data["fullname"],
        "credentials": [{
            "type": "password",
            "value": user_data["password"].get_secret_value(),
            "temporary": False
        }],
        # Roles are assigned in a separate step via the admin API, but this is the initial user object.
    }
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            # Create user
            create_response = await client.post(USERS_URL, json=kc_payload, headers=headers)
            create_response.raise_for_status()

            # The response does not contain the UID, it is in the 'Location' header.
            location_header = create_response.headers.get("Location", "")
            if not location_header:
                 raise Exception("Keycloak did not return the user location header.")
            
            # Extract UUID from Location header (e.g., /admin/realms/helixnet/users/0f1d...)
            keycloak_uid = location_header.split("/")[-1]
            
            # 3. Assign roles (assuming 'helix-web-app' client roles for simplicity)
            # This is complex and often done via Keycloak's roles endpoint. 
            # For brevity and focusing on the seeding issue, we assume the default client roles apply, 
            # or a separate admin client method handles this. We focus on the user creation here.
            
            logger.info(f"✨ Keycloak user '{user_data['username']}' created with UID: {keycloak_uid}")
            return keycloak_uid

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409: # Conflict, user already exists
            logger.warning(f"Keycloak user '{user_data['username']}' already exists (409 Conflict). Skipping creation.")
            # We would search for the user here and return their UID, but for simplicity, we treat this as a seed failure if the DB doesn't have it.
            # In a real app, you'd fetch the existing user's ID.
            raise HTTPException(status_code=409, detail=f"User already exists in Keycloak.")
        logger.error(f"Keycloak user creation failed (HTTP {e.response.status_code}): {e.response.text}", exc_info=False)
        raise
    except Exception as e:
        logger.error(f"Keycloak user creation failed: {e}", exc_info=True)
        raise

# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Startup Logic)
# ======================================================================

async def create_initial_users(db: AsyncSession) -> None:
    """Creates initial users in the database and in Keycloak."""
    logger.info("🌱 Starting initial user seeding process...")

    # --- 1. Define initial users ---
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
    
    admin_token = await get_keycloak_admin_token()
    if not admin_token:
        logger.error("🚨 Cannot proceed with user seeding: Keycloak Admin Token missing.")
        return

    for user_data in initial_users_data:
        username = user_data["username"]
        
        # --- 2. Idempotency Check (Check DB first) ---
        stmt = select(User).where(User.username == username)
        db_user_result = await db.execute(stmt)
        if db_user_result.scalar_one_or_none():
            logger.info(f"User '{username}' already exists in DB. Skipping Keycloak and DB creation.")
            continue

        logger.info(f"Attempting to seed new user: {username}...")
        
        try:
            # --- 3. Create User in Keycloak ---
            # NOTE: We skip the role assignment API call here for brevity, focusing on the user creation.
            keycloak_uid = await create_keycloak_user(
                admin_token=admin_token, 
                user_data={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "fullname": user_data["fullname"],
                },
                initial_roles=user_data["roles"]
            )
            
            # --- 4. Create User in Local DB ---
            new_user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"].get_secret_value()),
                fullname=user_data["fullname"],
                is_active=True,
                is_admin=user_data["is_admin"],
                keycloak_id=keycloak_uid, # Crucially link to Keycloak UID
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add(new_user)
            await db.commit()
            logger.info(f"💾 User '{username}' successfully created in DB and linked to Keycloak.")

        except HTTPException as e:
            # Catch 409 from Keycloak if implemented to handle the case where Keycloak has the user, but DB doesn't.
            logger.warning(f"Seeding failed for '{username}' due to Keycloak error: {e.detail}. Continuing.")
        except Exception as e:
            logger.error(f"FATAL ERROR during user seeding for '{username}': {e}", exc_info=True)
            await db.rollback()

    logger.info("✅ Initial user seeding process completed.")
    # The return None is implicit

# ======================================================================
# 🧑‍💻 ASYNC USER SERVICE (The Class the Router Needs)
# ======================================================================

class AsyncUserService:
    """
    Core service layer for handling all business logic related to the User model.
    """
    
    def __init__(self, db: AsyncSession):
        """Initializes the service with the database session."""
        self.db = db

    async def register_new_user(self, user_data: UserCreate) -> User:
        """Handles user registration."""
        logger.info(f"Attempting registration for {user_data.username}")
        # 1. Check if user already exists
        result = await self.db.execute(select(User).where(or_(User.email == user_data.email, User.username == user_data.username)))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email or username already exists.")

        # In a real application, step 2 (Keycloak user creation) would occur here using an injected Admin Token.
        # For this setup, we assume users are created via the Keycloak UI or the above seeding script only.

        # 3. Create local DB user
        new_user = User(
            id=uuid.uuid4(),
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password.get_secret_value()),
            fullname=user_data.fullname,
            is_active=True,
            is_admin=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            # keycloak_id=keycloak_uid # Must be filled from Keycloak response
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_user_profile(self, user_id: uuid.UUID, update_data: UserUpdate) -> Optional[User]:
        """Updates a user's profile."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        update_data_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_data_dict.items():
            if key == "password":
                user.hashed_password = get_password_hash(value.get_secret_value()) # Ensure SecretStr is unwrapped
            else:
                setattr(user, key, value)
        
        user.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieves a single user by their unique ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
        
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Retrieves a paginated list of all users."""
        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Deletes a user from the database and keycloak (optional)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            # Keycloak deletion logic would go here
            await self.db.delete(user)
            await self.db.commit()
            return True
        return False
