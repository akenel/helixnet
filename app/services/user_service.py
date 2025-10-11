# app/services/user_service.py 
"""
Service layer functions for user management (creation, retrieval, hashing, auth).
app/services/user_service.py
This handles all business logic interaction with the User model and external services (JWT/Bcrypt).
"""
import uuid
import logging
import traceback
from typing import List, Optional, Dict, Any

# 🔑 CRITICAL AUTH & TIME IMPORTS
from datetime import datetime, UTC # Use UTC for database consistency
from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes # Used in the dependency function  💡 Added OAuth2PasswordBearer

# 💾 DATABASE AND CORE IMPORTS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.database import get_db_session

# 🔑 CRITICAL AUTH IMPORTS
from jose import JWTError, jwt # 💡 Added missing 'jwt' import for token decoding

# 💾 DATABASE AND CORE IMPORTS
from app.core.security import ALGORITHM, SECRET_KEY, verify_password
from app.db.models.user_model import User # ⚠️ IMPORTANT: Assumes User model is correct

# 🛡️ DEFINE AUTH SCHEME (Fixes NameError)
# This handles the extraction of the Bearer token from the request header.
from app.core.security import oauth2_scheme

# --- 🛠️ Configuration and Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 🛡️ SECURITY UTILITY IMPORTS (Centralized from core/security.py)
from app.core.security import (
    ALGORITHM,          # Used for JWT decoding
    SECRET_KEY,         # Used for JWT decoding
    verify_password,    # Used in authenticate_user
    get_password_hash,  # Used in create_user and create_initial_users
    oauth2_scheme,      # Used in get_current_user dependency
)

# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Business Logic)
# ======================================================================

async def create_initial_users(db: AsyncSession) -> None:
    """
    🚀 Creates initial users in the database if they don't exist (for development).
    """
    logger.info("🌱 Starting initial user seeding process...")
    initial_users = [
        {"email": "admin@helix.net", "password": "admin", "is_active": True, "is_admin": True},
        {"email": "demo@helix.net", "password": "demo", "is_active": True},
        {"email": "test@helix.net", "password": "test", "is_active": True},
    ]

    try:
        for user_data in initial_users:
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                # 🎯 USES IMPORTED get_password_hash
                hashed_password = get_password_hash(user_data["password"]) 
                
                db_user = User(
                    id=uuid.uuid4(),
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    is_active=user_data.get("is_active", True),
                    is_admin=user_data.get("is_admin", False),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                db.add(db_user)
                logger.info(f"✨ Created user: {user_data['email']}")
            else:
                logger.info(f"👉 User already exists: {user_data['email']}")

        await db.commit()
        logger.info("✅ Initial user seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ CRITICAL Error during user seeding: {e}")
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        await db.rollback()
        raise

# ======================================================================
# 💾 DATABASE CRUD OPERATIONS
# ======================================================================
async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """
    🔍 Get a user by their ID.
    """
    logger.info(f"🔍 [USER_SVC] Retrieving user by ID: {user_id}")
    # 🐛 FIX: Use User model in select statement
    stmt = select(User).where(User.id == user_id) 
    result = await db.scalars(stmt)
    user = result.first()
    return user

# ======================================================================
# 👤 users by email FOR CURRENT USER
# ======================================================================
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    📧 Asynchronously retrieves a user from the database by their email address.
    """
    logger.info(f"🔍 [USER_SVC] Attempting to retrieve user by email: '{email}'.")
    # 🐛 FIX: Use User model in select statement
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"✅ [USER_SVC] User FOUND for email: '{email}'.")
    else:
        logger.warning(f"❌ [USER_SVC] User NOT found for email: '{email}'.")

    return user


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[User]:
    """
    📚 Get a list of users with pagination.
    """
    logger.info(f"📚 [USER_SVC] Fetching users (skip: {skip}, limit: {limit}).")
    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.scalars(stmt)
    return list(result.all())

# ======================================================================
# 💾 DATABASE CRUD OPERATIONS (Business Logic)
# ======================================================================
# ... (get_user_by_id, get_user_by_email, get_users - remain unchanged)
async def create_user(db: AsyncSession, user_in: Any) -> User:
    """
    ✨ Create a new user, checking for existence and hashing the password.
    Note: user_in should be a Pydantic UserCreate schema.
    """
    logger.info(f"✨ [USER_SVC] Starting creation of new user: '{user_in.email}'.")

    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        logger.error(
            f"⚠️ [USER_SVC] Creation failed: User already exists for '{user_in.email}'."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        # Check if attribute exists on user_in (Pydantic schema)
        is_active=getattr(user_in, 'is_active', True), 
        is_admin=getattr(user_in, 'is_admin', False),
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"🥳 [USER_SVC] User creation complete! New User ID: {db_user.id}.")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user creation for {user_in.email}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user creation: {e}",
        )

# ======================================================================
# 👤 Updates  FOR CURRENT USER
# ======================================================================
async def update_user(
    db: AsyncSession, user_id: uuid.UUID, user_update: Any
) -> Optional[User]:
    """
    ✏️ Update a user's information.
    Note: user_update should be a Pydantic UserUpdate schema.
    """
    logger.info(f"✏️ [USER_SVC] Starting update for User ID: {user_id}.")
    try:
        # 🐛 FIX: Use User model for select statement and primary key matching
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await db.scalars(stmt)
        db_user = result.first()

        if not db_user:
            logger.warning(f"❌ [USER_SVC] Update failed: User ID {user_id} not found.")
            return None

        # Pydantic utility to get changed fields
        update_data = user_update.model_dump(exclude_unset=True) 

        if "password" in update_data and update_data["password"] is not None:
            logger.info("🔑 [USER_SVC] Password field detected; hashing new password.")
            setattr(
                db_user,
                "hashed_password",
                get_password_hash(update_data.pop("password")),
            )

        # Apply updates to the ORM object
        for key, value in update_data.items():
            if value is not None:
                setattr(db_user, key, value)
        
        # Ensure updated_at is updated manually if not configured via ORM hook
        db_user.updated_at = datetime.now(UTC) 

        await db.commit()
        await db.refresh(db_user)
        logger.info(f"💾 [USER_SVC] User ID {user_id} updated successfully.")
        return db_user

    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user update for {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user update: {e}",
        )

# ======================================================================
# 👤 Delete  FOR CURRENT USER
# ======================================================================
async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """
    🗑️ Delete a user by their ID.
    """
    logger.warning(f"🗑️ [USER_SVC] Attempting to DELETE User ID: {user_id}.")
    try:
        # 🐛 FIX: Ensure delete statement uses User model and correct WHERE clause
        stmt = delete(User).where(User.id == user_id) 
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount > 0:
            logger.info(
                f"✅ [USER_SVC] Deleted {result.rowcount} user(s) with ID {user_id}."
            )
        else:
            logger.warning(
                f"❓ [USER_SVC] Delete attempted but no rows were found for ID {user_id}."
            )

        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user deletion for {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user deletion: {e}",
        )

# ======================================================================
# 👤 Authentication FOR CURRENT USER
# ======================================================================
async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[Dict[str, Any]]:
    """
    🔓 Looks up user by email and verifies the password hash for login.
    """
    logger.info(f"🔓 [AUTH_SVC] Starting authentication attempt for email: '{email}'.")

    user = await get_user_by_email(db, email)

    if not user:
        logger.warning("🚫 [AUTH_SVC] Authentication failed: User not found in DB.")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(
            "❌ [AUTH_SVC] Authentication failed: Incorrect password provided."
        )
        return None

    if not user.is_active:
        logger.warning(
            f"🛑 [AUTH_SVC] Authentication denied: User '{email}' is inactive."
        )
        return None

    # Success! Return the essential data required for JWT creation.
    logger.info(
        f"🎉 [AUTH_SVC] Authentication successful for user ID: {user.id}. Returning payload."
    )
    return {
        "sub": str(user.id), # 'sub' is the standard field for the subject/user ID
        "email": user.email,
        "is_active": user.is_active,
        "scopes": ["read"] + (["admin"] if user.is_admin else [])
    }

# ======================================================================
# 👤 DEPENDENCY FOR CURRENT USER
# ======================================================================

async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db_session),
    # ✅ FIX: oauth2_scheme is now defined globally
    token: str = Depends(oauth2_scheme), 
) -> User: # 💡 Returning the ORM model for service layer consistency
    """
    🔑 Dependency function to validate the JWT token, fetch the user,
    and verify the required security scopes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": f"Bearer scope={security_scopes.scope_str}"}, # 💡 Includes scopes
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id_str: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])

        if user_id_str is None:
            raise credentials_exception
        
        # Convert user_id_str back to UUID for database lookup
        user_id = uuid.UUID(user_id_str)

    except JWTError:
        logger.error("💥 [AUTH_DEP] JWT Error: Token invalid or expired.")
        raise credentials_exception
    except ValueError:
        logger.error("💥 [AUTH_DEP] User ID in token is not a valid UUID.")
        raise credentials_exception

    # 💾 Fetch user from the database.
    # 🐛 FIX: Use User model for select statement
    stmt = select(User).where(User.id == user_id) 
    result = await db.scalars(stmt)
    user = result.first()

    if user is None:
        logger.warning(f"🚫 [AUTH_DEP] User ID {user_id} found in token, but not in DB.")
        raise credentials_exception
    
    if not user.is_active:
        logger.warning(f"🚫 [AUTH_DEP] User ID {user_id} is inactive.")
        raise credentials_exception

    # 🧐 Scope Check: Ensure the user's token has *all* required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            logger.warning(f"🚫 [AUTH_DEP] User {user.email} missing required scope: {scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: Missing required scope '{scope}'",
            )

    # ✅ Return the ORM user object
    return user
############################################################################