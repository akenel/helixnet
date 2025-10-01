"""
Service layer functions for user management (creation, retrieval, hashing).
This version uses the 'bcrypt' library directly, bypassing 'passlib'
to resolve dependency conflicts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
import uuid
import bcrypt  # Direct import of the bcrypt library for hashing
from fastapi import HTTPException, status
# We import the User model directly from its file and alias it for clarity,
from app.db.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate

# --- Hashing and Verification Functions (Synchronous) ---
# NOTE: We have completely removed the passlib.context.CryptContext 
# to solve the repeated startup errors.

def get_password_hash(password: str) -> str:
    """
    Hashes a password using the bcrypt library directly.
    Requires password bytes as input and returns a utf-8 string hash.
    """
    # 1. Truncate the password to 72 bytes (bcrypt limit) and encode to bytes
    password_bytes = password[:72].encode('utf-8')
    
    # 2. Generate a salt and hash the password
    # gensalt() safely handles the default settings for rounds
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    # 3. Decode back to string for storage in the database
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hash using the bcrypt library directly.
    Requires both inputs to be encoded to bytes.
    """
    try:
        # Encode the inputs to bytes
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Check the password
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except ValueError:
        # Catches errors if the hash is malformed (e.g., wrong length or format)
        return False


# --- Database Service Functions (Asynchronous) ---

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[UserModel]:
    """Get a user by their ID."""
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.scalars(stmt)
    return result.first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """Get a user by their email address."""
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.scalars(stmt)
    return result.first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserModel]:
    """Get a list of users with pagination."""
    stmt = (
        select(UserModel)
        .order_by(UserModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.scalars(stmt)
    return list(result.all())

async def create_user_service(db: AsyncSession, user_in: UserCreate) -> UserModel:
    """Create a new user, checking for existence and hashing the password."""
    
    # 1. Check if user already exists
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # 2. Hash the password (using the direct bcrypt function)
    hashed_password = get_password_hash(user_in.password)

    # 3. Create the database model instance
    db_user = UserModel(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=user_in.is_active if user_in.is_active is not None else True
    )
    
    try:
        # 4. Add to session and commit
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        await db.rollback()
        # In a real API, you would log the error before raising a friendly HTTP exception.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user creation: {e}"
        )

async def update_user_service(db: AsyncSession, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[UserModel]:
    """Update a user's information."""
    try:
        # Use db.scalars for select queries with a single entity type
        stmt = select(UserModel).where(UserModel.id == user_id).with_for_update()
        result = await db.scalars(stmt)
        db_user = result.first()
        
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            if key == "password" and value is not None:
                # Hash new password before setting
                setattr(db_user, "hashed_password", get_password_hash(value))
            elif value is not None:
                setattr(db_user, key, value)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user update: {e}"
        )

async def delete_user_service(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Delete a user by their ID."""
    try:
        stmt = delete(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error during user deletion: {e}"
        )
