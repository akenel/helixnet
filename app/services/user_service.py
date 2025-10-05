"""
Service layer functions for user management (creation, retrieval, hashing, auth).
This consolidated version uses direct bcrypt for hashing and includes rich logging.
"""
import uuid
import logging
from typing import List, Optional, Dict, Any 
import traceback # Added for detailed logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status

import bcrypt 
from datetime import datetime

# --- CRITICAL IMPORTS ---
# We use UserModel consistently for the SQLAlchemy model
from app import db
from app.db.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate

# --- Setup Logger for Debugging ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 

# ----------------------------------------------------------------------
# HASHING AND VERIFICATION UTILITIES (Synchronous)
# ----------------------------------------------------------------------

def get_password_hash(password: str) -> str:
    """
    Hashes a password using the bcrypt library directly.
    """
    logger.debug("🛡️ [SECURITY] Hashing password with bcrypt.")
    # Safety: ensure password length is limited before encoding
    password_bytes = password[:72].encode('utf-8')
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hash using the bcrypt library directly.
    """
    try:
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except ValueError:
        # Occurs if the hash is malformed or not a valid bcrypt hash
        logger.error("🚨 [SECURITY] Failed verification due to malformed hash.")
        return False
    except Exception as e:
        logger.error(f"❌ Error during verify_password: {str(e)}")
        return False


async def create_initial_users(db: AsyncSession) -> None:
    """
    Creates initial users in the database if they don't exist.
    This function should be called during application startup.
    """
    logger.info("🌱 Starting initial user seeding process...")
    
    # Define initial users with their roles
    initial_users = [
        {"email": "admin@helix.net", "password": "admin", "is_active": True},
        {"email": "demo@helix.net", "password": "demo", "is_active": True},
        {"email": "test@helix.net", "password": "test", "is_active": True},
        {"email": "user@helix.net", "password": "user", "is_active": True},
        {"email": "marcel@helix.net", "password": "marcel", "is_active": True}
    ]
    
    try:
        for user_data in initial_users:
            # Check if user already exists
            result = await db.execute(
                select(UserModel).where(UserModel.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none() 
            
            if not existing_user:
                # Create new user if doesn't exist
                hashed_password = get_password_hash(user_data["password"]) 
                db_user = UserModel(
                    id=uuid.uuid4(),
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    is_active=user_data["is_active"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(db_user)
                logger.info(f"✨ Created user: {user_data['email']}")
            else:
                logger.info(f"👉 User already exists: {user_data['email']}")
        
        # Commit the transaction once for all users
        await db.commit() 
        logger.info("✅ Initial user seeding completed successfully!")
        
    except Exception as e:
        # Catch any database errors, log them, roll back, and raise
        logger.error(f"❌ CRITICAL Error during user seeding: {e}")
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        await db.rollback()
        raise


# ----------------------------------------------------------------------
# DATABASE SERVICE FUNCTIONS (Asynchronous)
# ----------------------------------------------------------------------

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
    """
    🔍 Get a user by their ID.
    """
    logger.info(f"🔍 [USER_SVC] Retrieving user by ID: {user_id}")
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.scalars(stmt)
    user = result.first()
    if user:
        logger.info(f"✅ [USER_SVC] User ID {user_id} found.")
    else:
        logger.warning(f"❌ [USER_SVC] User ID {user_id} NOT found.")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """
    🔍 Asynchronously retrieves a user from the database by their email address.
    """
    logger.info(f"🔍 [USER_SVC] Attempting to retrieve user by email: '{email}'.")
    
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        logger.info(f"✅ [USER_SVC] User FOUND for email: '{email}'. Proceeding to auth/password check.")
    else:
        logger.warning(f"❌ [USER_SVC] User NOT found for email: '{email}'. Auth will fail.")
            
    return user


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserModel]:
    """
    📚 Get a list of users with pagination.
    """
    logger.info(f"📚 [USER_SVC] Fetching users (skip: {skip}, limit: {limit}).")
    stmt = (
        select(UserModel)
        .order_by(UserModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return list(result.all())


async def create_user_service(db: AsyncSession, user_in: UserCreate) -> UserModel:
    """
    ✨ Create a new user, checking for existence and hashing the password.
    """
    logger.info(f"✨ [USER_SVC] Starting creation of new user: '{user_in.email}'.")

    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        logger.error(f"⚠️ [USER_SVC] Creation failed: User already exists for '{user_in.email}'.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # Hash the password 
    hashed_password = get_password_hash(user_in.password)

    db_user = UserModel(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=user_in.is_active if user_in.is_active is not None else True
    )
    
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"🥳 [USER_SVC] User creation complete! New User ID: {db_user.id}.")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(f"💥 [USER_SVC] Database error during user creation for {user_in.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user creation: {e}"
        )


async def update_user_service(db: AsyncSession, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[UserModel]:
    """
    ✏️ Update a user's information.
    """
    logger.info(f"✏️ [USER_SVC] Starting update for User ID: {user_id}.")
    try:
        stmt = select(UserModel).where(UserModel.id == user_id).with_for_update()
        result = await db.scalars(stmt)
        db_user = result.first()
        
        if not db_user:
            logger.warning(f"❌ [USER_SVC] Update failed: User ID {user_id} not found.")
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"] is not None:
            logger.info("🔑 [USER_SVC] Password field detected; hashing new password.")
            setattr(db_user, "hashed_password", get_password_hash(update_data.pop("password")))
        
        for key, value in update_data.items():
            if value is not None:
                setattr(db_user, key, value)

        await db.commit()
        await db.refresh(db_user)
        logger.info(f"💾 [USER_SVC] User ID {user_id} updated successfully.")
        return db_user

    except Exception as e:
        await db.rollback()
        logger.error(f"💥 [USER_SVC] Database error during user update for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user update: {e}"
        )


async def delete_user_service(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """
    🗑️ Delete a user by their ID.
    """
    logger.warning(f"🗑️ [USER_SVC] Attempting to DELETE User ID: {user_id}.")
    try:
        stmt = delete(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount > 0:
            logger.info(f"✅ [USER_SVC] Deleted {result.rowcount} user(s) with ID {user_id}.")
        else:
            logger.warning(f"❓ [USER_SVC] Delete attempted but no rows were found for ID {user_id}.")

        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"💥 [USER_SVC] Database error during user deletion for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user deletion: {e}"
        )

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    🔓 Looks up user by email and verifies the password hash for login.
    """
    logger.info(f"🔓 [AUTH_SVC] Starting authentication attempt for email: '{email}'.")

    # 1. Fetch user object/data from the DB
    user = await get_user_by_email(db, email) 
    
    if not user:
        logger.warning("🚫 [AUTH_SVC] Authentication failed: User not found in DB.")
        return None 

    # 2. Verify password against the hashed_password stored in the user object
    if not verify_password(password, user.hashed_password):
        logger.warning("❌ [AUTH_SVC] Authentication failed: Incorrect password provided.")
        return None 
    
    if not user.is_active:
        logger.warning(f"🛑 [AUTH_SVC] Authentication denied: User '{email}' is inactive.")
        return None

    # 3. Success! Return the essential data required for JWT creation.
    logger.info(f"🎉 [AUTH_SVC] Authentication successful for user ID: {user.id}. Returning payload.")
    return {
        "id": str(user.id), 
        "email": user.email,
        "is_active": user.is_active,
        # Add role/permissions here if needed
    }
