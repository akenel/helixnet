"""
Service layer functions for user management (creation, retrieval, hashing, auth).
This handles all business logic interaction with the User model and database CRUD.
"""
import uuid
import logging
import traceback
from typing import List, Optional, Any
from datetime import datetime, timezone, UTC 

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# 💾 DATABASE AND CORE IMPORTS
from app.db.models.user_model import User 
from app.core.security import get_password_hash # Only need hashing utility here
from app.schemas.user_schema import UserCreate, UserUpdate

# -----------------------------------------------------------------------------
# --- 🛠️ Configuration and Setup ---
# -----------------------------------------------------------------------------
logger = logging.getLogger("helix.service.user")
logger.setLevel(logging.INFO)

# Helper for initial setup logging
def _log(level: str, message: str, **extra):
    """Dual-log helper for immediate stdout and structured logging."""
    print(f"[helix.user_svc][{level.upper()}] {datetime.now(timezone.utc).isoformat()} - {message}", flush=True)
    if hasattr(logger, level):
        getattr(logger, level)(message, extra=extra)

# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Business Logic)
# ======================================================================

async def create_initial_users(db: AsyncSession) -> None:
    """
    🚀 Creates initial users in the database if they don't exist (for development).
    This runs at application startup.
    """
    _log("info", "🌱 Starting initial user seeding process...")
    
    initial_users = [
        {"email": "admin@helix.net", "password": "admin", "is_active": True, "is_admin": True, "fullname": "Admin User"},
        {"email": "demo@helix.net", "password": "demo", "is_active": True, "is_admin": False, "fullname": "Demo User"},
        # Add 'is_admin' instead of 'is_admin' to match typical ORM model names
        {"email": "cn@helix.net", "password": "CN", "is_active": True, "is_admin": True, "fullname": "Super CN"}, 
    ] 
    try:
        for user_data in initial_users:
            email = user_data["email"]
            is_admin = user_data.get("is_admin", False)
            username = email.split('@')[0]
            
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                hashed_password = get_password_hash(user_data["password"]) 
        
                db_user = User(
                    id=uuid.uuid4(),
                    email=email,
                    username=username,
                    hashed_password=hashed_password,
                    is_active=user_data.get("is_active", True),
                    is_admin=is_admin,
                    fullname=user_data.get("fullname"),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                db.add(db_user)
                _log("info", f"✨ Created new account: {email} | Admin: {is_admin}")
            else:
                _log("info", f"👉 Account already exists: {email}")

        await db.commit()
        _log("info", "✅ Initial user seeding completed successfully!")

    except Exception as e:
        _log("error", f"❌ CRITICAL Error during user seeding: {e}")
        _log("error", f"❌ Full traceback:\n{traceback.format_exc()}")
        await db.rollback()
        # Do not raise here, just log, so startup can continue if DB is healthy
        # raise 

# ======================================================================
# 💾 UserService CLASS (The fix for your import error!)
# ======================================================================

class UserService:
    """
    Manages all business logic and data access for User entities.
    """
    def __init__(self):
        """Service layer is stateless; no special initialization needed here."""
        pass

    async def get_user_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """
        🔍 Get a user by their ID.
        """
        logger.info(f"🔍 Retrieving user by ID: {user_id}")
        stmt = select(User).where(User.id == user_id) 
        result = await db.scalars(stmt)
        return result.first()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        📧 Asynchronously retrieves a user from the database by their email address.
        """
        logger.info(f"🔍 Attempting to retrieve user by email: '{email}'.")
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        📚 Get a list of users with pagination.
        """
        logger.info(f"📚 Fetching users (skip: {skip}, limit: {limit}).")
        stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await db.scalars(stmt)
        return list(result.all())

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        ✨ Create a new user, checking for existence and hashing the password.
        """
        logger.info(f"✨ Starting creation of new user: '{user_in.email}'.")

        existing_user = await self.get_user_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
            
        username_to_use = user_in.email.split('@')[0]

        hashed_password = get_password_hash(user_in.password)

        db_user = User(
            email=user_in.email,
            username=username_to_use,
            fullname=user_in.fullname,
            # Derive is_admin from roles list for consistency, if your ORM supports it
            is_admin="ADMIN" in [r.upper() for r in user_in.roles], 
            hashed_password=hashed_password,
            is_active=True, 
        )

        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            logger.info(f"🥳 User creation complete! New User ID: {db_user.id}.")
            return db_user
        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Database error during user creation for {user_in.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during user creation.",
            )

    async def update_user(
        self, db: AsyncSession, user_id: uuid.UUID, user_update: UserUpdate
    ) -> Optional[User]:
        """
        ✏️ Update a user's information.
        """
        logger.info(f"✏️ Starting update for User ID: {user_id}.")
        try:
            # Use 'select for update' if concurrent writes are a concern
            stmt = select(User).where(User.id == user_id) 
            result = await db.scalars(stmt)
            db_user = result.first()

            if not db_user:
                return None

            update_data = user_update.model_dump(exclude_unset=True) 

            if "password" in update_data and update_data["password"] is not None:
                logger.info("🔑 Password field detected; hashing new password.")
                setattr(
                    db_user,
                    "hashed_password",
                    get_password_hash(update_data.pop("password")),
                )

            # Apply updates from Pydantic model
            for key, value in update_data.items():
                if value is not None:
                    setattr(db_user, key, value)
            
            db_user.updated_at = datetime.now(UTC) 

            await db.commit()
            await db.refresh(db_user)
            logger.info(f"💾 User ID {user_id} updated successfully.")
            return db_user

        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Database error during user update for {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during user update.",
            )

    async def delete_user(self, db: AsyncSession, user_id: uuid.UUID) -> bool:
        """
        🗑️ Delete a user by their ID.
        """
        logger.warning(f"🗑️ Attempting to DELETE User ID: {user_id}.")
        try:
            stmt = delete(User).where(User.id == user_id) 
            result = await db.execute(stmt)
            await db.commit()

            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"💥 Database error during user deletion for {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during user deletion.",
            )
user_service = UserService() 