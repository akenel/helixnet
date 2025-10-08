# app/routes/users_router.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

# --- SECURITY ---
from app.core.security import get_current_user
from app.schemas.user import UserInDB
# --- END SECURITY ---

from app.db.database import get_db_session # Dependency is imported correctly
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import (
    get_user_by_email,
    get_users,
    get_user_by_id,
    create_user_service,
    update_user_service,
    delete_user_service
)

logger = logging.getLogger(__name__) # Initialize logger

users_router = APIRouter(
    tags=["🥵️ Users : users_router"],
    responses={404: {"description": "User not found"}}
)

# ----------------------------------------------------
# ⚠️ UNSECURED ENDPOINT: CREATE USER
# ----------------------------------------------------
@users_router.post(
        "/", 
        response_model=UserInDB, 
        status_code=status.HTTP_201_CREATED
        )
async def create_user_endpoint(
    user: UserCreate,
    # ✅ CORRECT USAGE: FastAPI resolves Depends(get_db_session) to AsyncSession
    db: AsyncSession = Depends(get_db_session)
) -> UserInDB:
    # Service function receives the actual AsyncSession object (db)
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await create_user_service(db, user)


# ----------------------------------------------------
# ✅ SECURED ENDPOINTS: READ, UPDATE, DELETE (CRUD)
# ----------------------------------------------------

@users_router.get(
        "/me", 
        response_model=UserInDB,
        summary="Get Current User Profile"
                  
 )
async def read_users_me(
    # 💥 THE GATEKEEPER IS APPLIED! This route MUST be defined before /{user_id}
    current_user: UserInDB = Depends(get_current_user) 
) -> UserInDB:
    """Retrieves the currently authenticated user's profile."""
    # Get user information from the object returned by the dependency
    return current_user 

@users_router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    # 💥 THE GATEKEEPER IS APPLIED!
    current_user: UserInDB = Depends(get_current_user) 
) -> UserInDB:
    """Retrieves a user by UUID."""
    # (Optional: Add logic to check if current_user.id == user_id or is_admin)
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@users_router.get(
        "/", 
        response_model=List[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    # 💥 THE GATEKEEPER IS APPLIED!
    current_user: UserInDB = Depends(get_current_user) 
) -> List[UserInDB]:
    """
    Retrieves a list of all users in the system. Requires authentication.
    """
    logger.debug(f"[USER_ROUTE] Listing users for authenticated user: {current_user.email}")
    # (Optional: Add a check here if only admins can list all users)
    return await get_users(db, skip=skip, limit=limit)

@users_router.patch("/{user_id}", response_model=UserInDB)
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    # 💥 THE GATEKEEPER IS APPLIED!
    current_user: UserInDB = Depends(get_current_user) 
) -> UserInDB:
    # (CRITICAL: Add authorization check here)
    # Note: User IDs should be compared as strings or UUID objects consistently
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    user = await update_user_service(db, user_id, user_update)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    # 💥 THE GATEKEEPER IS APPLIED!
    current_user: UserInDB = Depends(get_current_user) 
):
    # (CRITICAL: Add authorization check here)
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    deleted = await delete_user_service(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
