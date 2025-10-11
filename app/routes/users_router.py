# app/routes/users_router.py
# ================================================================
# 🧱 HelixNet User Router — Clean, Secure, Fully Functional
# ================================================================
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# 🧩 Local Imports
from app.db.database import get_db_session  # ✅ Correct dependency
from app.db.models.user_model import User
from app.schemas.user_schema import UserCreate, UserRead, UserUpdate
from app.services.user_service import (
    get_current_user,
    get_user_by_id,
    get_users,
    update_user,
    delete_user,
)
from app.core.security import get_password_hash

# ================================================================
# ⚙️ Router Setup
# ================================================================
logger = logging.getLogger(__name__)
users_router = APIRouter()

# ================================================================
# 🧩 Public Endpoint — Create New User
# ================================================================
@users_router.post(
    "/register",  # ✅ FIX: Use a unique path for user creation/registration
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="🧩 Register a new user account"
)

async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    """
    🧩 Public endpoint: Create a new user.
    Automatically hashes password before saving.
    """
    logger.info(f"Attempting to create user: {user.email}")

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create and persist user
    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_admin=user.is_admin or False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"✅ User created successfully: {user.email}")
    return new_user


# ================================================================
# 🔒 Authenticated User — Get Profile (/me)
# ================================================================
@users_router.get("/me", response_model=UserRead, summary="Get Current User Profile")
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's profile."""
    return current_user


# ================================================================
# 🔒 Read a Specific User (by UUID)
# ================================================================
@users_router.get("/{user_id}", response_model=UserRead, summary="Get User by ID")
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a user by ID. Admin or owner only."""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ================================================================
# 🔒 Admin — List All Users
# ================================================================
@users_router.get("/", response_model=List[UserRead], summary="List all users (Admin only)")
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all users. Admin access required."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return await get_users(db, skip=skip, limit=limit)


# ================================================================
# 🔒 Update User
# ================================================================
@users_router.patch("/{user_id}", response_model=UserRead, summary="Update user details")
async def update_user_endpoint(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update an existing user. Admin or owner only."""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await update_user(db, user_id, user_update)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ================================================================
# 🔒 Delete User
# ================================================================
@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user_endpoint(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a user account. Admin or owner only."""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None
