# src/routes/users_router.py
"""
🧩 HelixNet User Management Router
Handles registration, profile, and admin user management routes.

✅ Fully async
✅ Integrates Keycloak proxy + database session
✅ Extensive logging for debugging
"""

import logging
from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import ClientSession

from src.core.local_auth_service import get_current_user, get_password_hash
from src.db.database import get_db_session
from src.db.models.user_model import UserModel
from src.schemas.user_schema import UserRead, UserCreate, UserUpdate
from src.services.user_service import AsyncUserService

# -----------------------------------------------------------------------------
# Logger Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
async def get_http_session() -> ClientSession:
    """Provide a managed aiohttp session."""
    session = ClientSession()
    try:
        yield session
    finally:
        await session.close()
        logger.debug("🔒 Closed aiohttp ClientSession after request.")


async def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    http_session: Annotated[ClientSession, Depends(get_http_session)],
) -> AsyncUserService:
    """Inject AsyncUserService with DB + HTTP session."""
    return AsyncUserService(db=db, http_session=http_session)

# -----------------------------------------------------------------------------
# FastAPI Router
# -----------------------------------------------------------------------------
users_router = APIRouter(prefix="/users", tags=["Users"])

UserService = Annotated[AsyncUserService, Depends(get_user_service)]
CurrentDBUser = Annotated[UserModel, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db_session)]

# -----------------------------------------------------------------------------
# Register New User
# -----------------------------------------------------------------------------
@users_router.post("/register", response_model=UserRead)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    http_session: ClientSession = Depends(get_http_session),
):
    service = AsyncUserService(db=db, http_session=http_session)
    return await service.create_local_user(user_data)

# -----------------------------------------------------------------------------
# Current User Profile
# -----------------------------------------------------------------------------
@users_router.get("/me", response_model=UserRead, summary="🔒 Get current user profile")
async def read_current_user(current_user: CurrentDBUser):
    logger.debug(f"👤 Profile requested for user: {current_user.email}")
    return current_user

# -----------------------------------------------------------------------------
# Update Current User Profile
# -----------------------------------------------------------------------------
@users_router.put("/me", response_model=UserRead, summary="🔒 Update current user profile")
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentDBUser,
    user_service: UserService,
):
    logger.info(f"🛠️ Updating profile for {current_user.email}")
    return await user_service.update_user_profile(current_user.id, update_data)

# -----------------------------------------------------------------------------
# Get User by ID
# -----------------------------------------------------------------------------
@users_router.get("/{user_id}", response_model=UserRead, summary="🔒 Get user by ID")
async def read_user(
    user_id: UUID,
    user_service: UserService,
    current_user: CurrentDBUser,
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

# -----------------------------------------------------------------------------
# List All Users (Admin Only)
# -----------------------------------------------------------------------------
@users_router.get("/", response_model=List[UserRead], summary="🔒 List all users (Admin only)")
async def list_users(
    admin_user: CurrentDBUser,
    user_service: UserService,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
):
    if not admin_user.is_admin:
        raise HTTPException(403, "Admin privileges required")
    users = await user_service.get_users(skip=skip, limit=limit)
    logger.debug(f"📊 Admin {admin_user.email} listed {len(users)} users")
    return users

# -----------------------------------------------------------------------------
# Delete User (Admin or Owner)
# -----------------------------------------------------------------------------
@users_router.delete("/{user_id}", status_code=204, summary="🔒 Delete user (Admin/Owner)")
async def delete_user(
    user_id: UUID,
    user_service: UserService,
    current_user: CurrentDBUser,
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    logger.info(f"🗑️ User {user_id} deleted by {current_user.email}")
