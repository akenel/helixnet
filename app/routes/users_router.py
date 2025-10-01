# app/routes/users_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db.database import get_db_session
from app.schemas.user import UserCreate, UserUpdate, UserInDB
# IMPORT THE NEW SERVICE LAYER
from app.services.user_service import (
    get_user_by_email,
    get_users,
    get_user_by_id,
    create_user_service, # Use the renamed service function
    update_user_service, # Use the renamed service function
    delete_user_service  # Use the renamed service function
)

# FIXED: Simplified APIRouter initialization
users_router = APIRouter(
    tags=["Users"], 
    responses={404: {"description": "User not found"}}
)

@users_router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint( # Renamed to avoid confusion with service function
    user: UserCreate,
    db: AsyncSession = Depends(get_db_session)
) -> UserInDB:
    # 1. Check for existing user using service layer
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # 2. Call the service layer to create the user
    return await create_user_service(db, user)

@users_router.get("/", response_model=List[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
) -> List[UserInDB]:
    # Call the service layer to retrieve users
    return await get_users(db, skip=skip, limit=limit)

@users_router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
) -> UserInDB:
    # Call the service layer to retrieve a single user
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@users_router.patch("/{user_id}", response_model=UserInDB)
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db_session)
) -> UserInDB:
    # Call the service layer to update the user
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
    db: AsyncSession = Depends(get_db_session)
):
    # Call the service layer to delete the user
    deleted = await delete_user_service(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

# REMOVE ALL SERVICE FUNCTIONS FROM THIS FILE