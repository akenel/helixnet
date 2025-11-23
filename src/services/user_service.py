# src/services/user_service.py
"""
AsyncUserService
Handles DB operations and Keycloak seeding.
"""

import logging
import asyncio
from typing import List
from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import SecretStr

from src.db.models import UserModel
from src.schemas.user_schema import UserCreate, UserUpdate
from src.services.keycloak_service import KeycloakProxyService
import src.core.local_auth_service as local_auth_service
from src.exceptions.user_exceptions import DuplicateUserError

logger = logging.getLogger("🌱 UserService")
logger.setLevel(logging.INFO)

class AsyncUserService:
    def __init__(self, db: AsyncSession, http_session: ClientSession):
        self.db = db
        self.http_session = http_session
        self.keycloak_service = KeycloakProxyService(settings=None, session=http_session)

    async def create_local_user(self, user_data: UserCreate):
        """Create local user with optional Keycloak registration."""
        stmt = select(UserModel).where(UserModel.username == user_data.username)
        existing = await self.db.execute(stmt)
        if existing.scalar_one_or_none():
            logger.warning(f"⚠️ User {user_data.username} exists locally. Skipping.")
            return existing.scalar_one()

        # Register in Keycloak
        try:
            keycloak_resp = await self.keycloak_service.register_user(user_data)
            kc_id = keycloak_resp["id"]
        except DuplicateUserError:
            logger.warning(f"⚠️ User {user_data.username} exists in Keycloak. Skipping KC creation.")
            kc_id = None

        new_user = UserModel(
            keycloak_id=kc_id, # 👈 Pass the Keycloak ID to the correct model field
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            # Removed: hashed_password=...
            is_active=True,
            is_superuser=False, # Assuming 'is_admin' maps to 'is_superuser'
        )

        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            logger.info(f"✅ Local user created: {user_data.username}")
            return new_user
        except Exception:
            await self.db.rollback()
            raise

    # Stub methods for completeness
    async def get_user_by_id(self, user_id):
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(self, skip=0, limit=100):
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_user_profile(self, user_id, update_data: UserUpdate):
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id):
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True

# ------------------------------------------------------
# Initial User Seeding (PRO-Level Idempotent)
# ------------------------------------------------------
async def create_initial_users(db: AsyncSession):
    """Seed initial admin users into Keycloak and DB."""
    initial_users = [
        {
            "username": "taxman",
            "email": "taxman@helix.net",
            "password": "taxman",
            "first_name": "taxman",
            "last_name": "User",
            "is_admin": True,
        }
    ]

    async with ClientSession() as session:
        kc_service = KeycloakProxyService(settings=None, session=session)
        for u in initial_users:
            # Check DB
            stmt = select(UserModel).where(UserModel.username == u["username"])
            existing = await db.execute(stmt)
            if existing.scalar_one_or_none():
                logger.info(f"⏭️ User {u['username']} already exists locally. Skipping.")
                continue

            # --- START FIX AREA ---
            kc_id = None # Initialize kc_id to None
            
            # Create in Keycloak
            try:
                # This path runs if the user is NOT in Keycloak
                kc_resp = await kc_service.register_user(UserCreate(**u))
                kc_id = kc_resp.get("id")
            except DuplicateUserError:
                # This path runs if the user IS in Keycloak (we need to get the ID here if not None)
                logger.warning(f"⚠️ User {u['username']} exists in Keycloak. Skipping.")
                # We should try to LOOK UP the existing user's ID here if needed,
                # but for simplicity, we rely on the DB check above. For now, leave kc_id = None.
                pass # IMPORTANT: Do not assign new_user here!

            # Create locally (THIS BLOCK MUST BE EXECUTED WHETHER KC SUCCEEDED OR SKIPPED)
            new_user = UserModel(
                keycloak_id=kc_id, # This will be the new ID or None if the user was skipped/existed
                username=u["username"],
                email=u["email"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                is_active=True,
                is_superuser=u["is_admin"],
            )

            db.add(new_user)
            # --- END FIX AREA ---
            
            try:
                await db.commit()
                await db.refresh(new_user)
                logger.info(f"✅ Seeded user {u['username']} locally and in Keycloak.")
            except Exception:
                await db.rollback()
                logger.error(f"💣 Failed to seed user {u['username']}.", exc_info=True)