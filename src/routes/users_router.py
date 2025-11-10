import logging
from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
from aiohttp import ClientSession

from src.core.local_auth_service import get_current_user
from src.db.database import get_db_session
from src.db.models.user_model import UserModel
from src.services.user_service import AsyncUserService
from src.schemas.user_schema import UserRead, UserCreate, UserUpdate
from src.exceptions.user_exceptions import DuplicateUserError

# Initialize logger
logger = logging.getLogger(__name__)

# Dependency to manage the aiohttp ClientSession
async def get_http_session() -> ClientSession:
    session = ClientSession()
    try:
        yield session
    finally:
        await session.close()
        logger.debug("Closed aiohttp ClientSession.")

# Dependency to provide the user service
async def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    http_session: Annotated[ClientSession, Depends(get_http_session)],
) -> AsyncUserService:
    return AsyncUserService(db=db, http_session=http_session)

# FastAPI router setup
users_router = APIRouter(prefix="/users")

# Type annotations for dependencies
UserService = Annotated[AsyncUserService, Depends(get_user_service)]
CurrentDBUser = Annotated[UserModel, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db_session)]

# Register new user
@users_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="🧩 Register a new user account"

)
async def register_new_user(
    user_data: UserCreate,
    user_service: UserService,
):
    logger.info(f"Attempting to register user: {user_data.email}")
    try:
        new_user = await user_service.register_new_user(user_data)
        return new_user
    except DuplicateUserError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User registration service is currently unavailable."
        )

# Get current user profile
@users_router.get("/me", response_model=UserRead, summary="🔒 Get details of the currently authenticated user.")
async def read_current_user(current_user: CurrentDBUser):
    return current_user

# Update current user profile
@users_router.put("/me", response_model=UserRead, summary="🔒 Update the profile of the currently authenticated user.")
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentDBUser,
    user_service: UserService,
):
    logger.info(f"Updating profile for user ID: {current_user.id}")
    updated_user = await user_service.update_user_profile(current_user.id, update_data)
    return updated_user

# Read a specific user (Admin or Owner only)
@users_router.get("/{user_id}", response_model=UserRead, summary="🔒 Get User by ID (Admin/Owner)")
async def read_user(
    user_id: UUID,
    user_service: UserService,
    current_user: CurrentDBUser,
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user profile.")
    
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# List all users (Admin only)
@users_router.get("/", response_model=List[UserRead], summary="🔒 List all users (Admin only)")
async def read_users(
    admin_user: CurrentDBUser,
    user_service: UserService,
    skip: int = Query(0, ge=0, description="The number of items to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="The maximum number of items to return"),
):
    if not admin_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required.")
    
    users = await user_service.get_users(skip=skip, limit=limit)
    return users

# Update specific user (Admin or Owner only)
@users_router.patch("/{user_id}", response_model=UserRead, summary="🔒 Update specific user details (Admin/Owner)")
async def update_user_endpoint(
    user_id: UUID,
    user_update: UserUpdate,
    user_service: UserService,
    current_user: CurrentDBUser,
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user.")
    
    updated_user = await user_service.update_user_profile(user_id, user_update)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user

# Delete user (Admin or Owner only)
@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="🔒 Delete user (Admin/Owner)")
async def delete_user_endpoint(
    user_id: UUID,
    user_service: UserService,
    current_user: CurrentDBUser,
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user.")

    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return None