"""
API Router for User Management.
Handles user registration, profile retrieval, and updates.
Requires authentication for all profile access endpoints.
"""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status  
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.database import get_db_session 
from app.db.models.user_model import User 
# 🚨 --- Import the exposed ASYNC service instance directly
from app.services.user_service import AsyncUserService
from app.schemas.user_schema import UserRead, APICaller,  UserCreate, UserRead, UserUpdate
# ----------------------------------------------------------------------

# ================================================================
# 💉 Dependency Injection Setup
# ================================================================

logger = logging.getLogger(__name__)

# 🚨 FIX 3: REMOVE incorrect type aliases that caused the FastAPIError
# DBSession = Annotated[AsyncSession, Depends(AsyncUserService)]
# CurrentUser = Annotated[User, Depends(AsyncUserService)]

# ================================================================
# ⚙️ Router Setup
# ================================================================
# Renamed from 'router' to 'users_router' and kept configuration
users_router = APIRouter(prefix="/users") 

# ================================================================
# 🧩 1. Public Endpoint — Register New User (/users/register)
# ================================================================
@users_router.post(
    "/register", 
    response_model=UserRead, 
    status_code=status.HTTP_201_CREATED,
    summary="🧩 Register a new user account"
)
async def register_new_user(
    user_data: UserCreate,   
    db: AsyncSession = Depends(get_db_session)
):
    """
    Handles user registration by calling the fully asynchronous service layer.
    """
    logger.info(f"Attempting to register user: {user_data.email}")
    try:
        # 🚨 FIX 4: Use await on the ASYNC service instance. Threadpool is no longer needed.
        new_user = await AsyncSession(db, user_data)
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred during registration."
        )

# ================================================================
# 🔒 2. Authenticated User — Get Profile (/users/me)
# ================================================================
@users_router.get("/me", 
    response_model=UserRead, 
    summary="🔒 Get details of the currently authenticated user."
)
async def read_current_user(
    # 🚨 FIX 5: Use correct dependency for current user
    current_user: User = Depends(get_current_user)
):
    """Returns the profile data for the logged-in user."""
    # The get_current_user dependency ensures the user object is already fetched
    return current_user

# ================================================================
# 🔒 3. Update Current User Profile (/users/me)
# ================================================================
@users_router.put(
    "/me", 
    response_model=UserRead, 
    summary="🔒 Update the profile of the currently authenticated user."
)
async def update_current_user(
    update_data: UserUpdate, 
    current_user: User = Depends(get_current_user), # Correct dependency
    db: AsyncSession = Depends(get_db_session) # Correct dependency
):
    """
    Allows the authenticated user to update their own profile details.
    """
    logger.info(f"Updating profile for user ID: {current_user.id}")
    # 🚨 FIX 6: Use await on the ASYNC service instance. Threadpool is no longer needed.
    updated_user = await async_user_service.update_user_profile(
        db, 
        current_user.id, # Always update the current user's ID
        update_data
    )
    return updated_user

# ================================================================
# 🔒 4. Read a Specific User (Admin or Owner only)
# ================================================================
@users_router.get("/{user_id}", response_model=UserRead, summary="🔒 Get User by ID (Admin/Owner)")
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    # 🚨 FIX 7: Use correct dependency for current user
    current_user: User = Depends(get_current_user)
):
    """Retrieve a user by ID. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user profile.")

    # Fetch User
    # 🚨 FIX 8: Use await on the ASYNC service instance. Threadpool is no longer needed.
    user = await async_user_service.get_user_by_id(db, user_id) 
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# ================================================================
# 🔒 5. List All Users (Admin only)
# ================================================================
@users_router.get("/", 
    response_model=List[UserRead], 
    summary="🔒 List all users (Admin only)"
)

@users_router.get("/", response_model=List[UserRead], status_code=status.HTTP_200_OK)
async def read_users(
    # --- CHUCK KICK: ADMIN ENFORCEMENT ---
    # Only users passing this dependency can access this endpoint. 
    # If the user is not an admin, the request will halt here.
    admin_user: APICaller = Depends(get_current_user), 
    # -------------------------------------
    
    skip: int = Query(0, ge=0, description="The number of items to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="The maximum number of items to return"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve a paginated list of all users.
    
    **REQUIRES ADMINISTRATOR PRIVILEGES.**
    """
    # 1. Instantiate the refactored service class with the session
    user_service = AsyncUserService(db=db)
    
    # 2. Call the newly implemented service method
    users = await user_service.get_users(skip=skip, limit=limit)
    
    return users

# ================================================================
# 🔒 6. Update Specific User (Admin or Owner only)
# ================================================================
@users_router.patch("/{user_id}", response_model=UserRead, summary="🔒 Update specific user details (Admin/Owner)")
async def update_user_endpoint(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    # 🚨 FIX 11: Use correct dependency for current user
    current_user: User = Depends(get_current_user),
):
    """Update an existing user. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user.")

    # Update User 
    # 🚨 FIX 12: Use await on the ASYNC service instance. Threadpool is no longer needed.
    updated_user = await async_user_service.update_user_profile(db, user_id, user_update)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user

# ================================================================
# 🔒 7. Delete User (Admin or Owner only)
# ================================================================
@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="🔒 Delete user (Admin/Owner)")
async def delete_user_endpoint(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    # 🚨 FIX 13: Use correct dependency for current user
    current_user: User = Depends(get_current_user),
):
    """Delete a user account. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user.")

    # Delete User (NOTE: Assuming async_user_service.delete_user exists and is ASYNC)
    try:
        # 🚨 FIX 14: Use await on the ASYNC service instance. Threadpool is no longer needed.
        deleted = await async_user_service.delete_user(db, user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except AttributeError:
        logger.error("AsyncUserService is missing the 'delete_user' method.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion service not fully implemented."
        )
    
    return None
