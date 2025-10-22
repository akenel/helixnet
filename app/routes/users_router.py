"""
API Router for User Management.
Handles user registration, profile retrieval, and updates.
Requires authentication for all profile access endpoints.
"""
import logging
from typing import List, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status  
from sqlalchemy.ext.asyncio import AsyncSession
# Import the Keycloak payload dependency alias from security (used indirectly by get_current_user)
from app.core.security import get_current_user
from app.db.database import get_db_session 
from app.db.models.user_model import UserModel
from app.services.user_service import AsyncUserService # The service class
from app.schemas.user_schema import UserRead, UserCreate, UserUpdate
from app.exceptions.user_exceptions import DuplicateUserError # Assuming a custom exception for clean Keycloak/DB errors
# ----------------------------------------------------------------------

# ================================================================
# 💉 Dependency Injection Setup
# ================================================================

logger = logging.getLogger(__name__)

# New Dependency: Provides a properly initialized AsyncUserService instance
async def get_user_service(db: AsyncSession = Depends(get_db_session)) -> AsyncUserService:
    """Provides an instance of the AsyncUserService tied to the current DB session."""
    return AsyncUserService(db=db)

# Alias for type annotation clarity in endpoints
UserService = Annotated[AsyncUserService, Depends(get_user_service)]

# Alias for type-hinting the authenticated user (assumes get_current_user returns the DB User model)
CurrentDBUser = Annotated[UserModel, Depends(get_current_user)]


# ================================================================
# ⚙️ Router Setup
# ================================================================
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
    user_service: UserService, # Inject the service instance
):
    """
    Handles user registration by creating the user in Keycloak, then synchronizing
    the resulting user record (with Keycloak-assigned ID) to the local database.
    """
    logger.info(f"Attempting to register user: {user_data.email}")
    try:
        # Use the service instance to perform the creation logic (Keycloak + DB)
        new_user = await user_service.create_user_keycloak_db(user_data)
        return new_user
    
    except DuplicateUserError as e:
        # Custom exception for clean error feedback (e.g., user already exists)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException as e:
        # Re-raise explicit HTTP exceptions from the service layer
        raise e
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        # Fallback for unexpected issues (e.g., Keycloak connection failure)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User registration service is currently unavailable."
        )

# ================================================================
# 🔒 2. Authenticated User — Get Profile (/users/me)
# ================================================================
@users_router.get("/me", 
    response_model=UserRead, 
    summary="🔒 Get details of the currently authenticated user."
)
async def read_current_user(
    current_user: CurrentDBUser # Use the type-hinted alias for the authenticated DB user
):
    """Returns the profile data for the logged-in user."""
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
    current_user: CurrentDBUser, # Use the type-hinted alias for the authenticated DB user
    user_service: UserService, # 🚨 FIX: Corrected dependency to use UserService
):
    """
    Allows the authenticated user to update their own profile details.
    """
    logger.info(f"Updating profile for user ID: {current_user.id}")
    
    # Use the service instance to update the profile (DB + Keycloak sync)
    updated_user = await user_service.update_user_profile(
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
    user_service: UserService, # Inject the service instance
    current_user: CurrentDBUser # Use the type-hinted alias for the authenticated DB user
):
    """Retrieve a user by ID. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this user profile.")

    # Fetch User
    user = await user_service.get_user_by_id(user_id) 
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# ================================================================
# 🔒 5. List All Users (Admin only)
# ================================================================
@users_router.get("/", 
    response_model=List[UserRead], 
    summary="🔒 List all users (Admin only)",
    status_code=status.HTTP_200_OK
)
async def read_users(
    # --- ADMIN ENFORCEMENT ---
    admin_user: CurrentDBUser, 
    # -------------------------
    user_service: UserService, # Inject the service instance
    skip: int = Query(0, ge=0, description="The number of items to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="The maximum number of items to return"),
):
    """
    Retrieve a paginated list of all users.
    
    **REQUIRES ADMINISTRATOR PRIVILEGES.**
    """
    # Explicit Admin Check (though it should ideally be handled by a dedicated dependency)
    if not admin_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required.")
        
    users = await user_service.get_users(skip=skip, limit=limit)
    return users

# ================================================================
# 🔒 6. Update Specific User (Admin or Owner only)
# ================================================================
@users_router.patch("/{user_id}", response_model=UserRead, summary="🔒 Update specific user details (Admin/Owner)")
async def update_user_endpoint(
    user_id: UUID,
    user_update: UserUpdate,
    user_service: UserService, # Inject the service instance
    current_user: CurrentDBUser, # Use the type-hinted alias for the authenticated DB user
):
    """Update an existing user. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user.")

    # Update User 
    updated_user = await user_service.update_user_profile(user_id, user_update)
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user

# ================================================================
# 🔒 7. Delete User (Admin or Owner only)
# ================================================================
@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="🔒 Delete user (Admin/Owner)")
async def delete_user_endpoint(
    user_id: UUID,
    user_service: UserService, # Inject the service instance
    current_user: CurrentDBUser, # Use the type-hinted alias for the authenticated DB user
):
    """Delete a user account. Requires Admin privileges or the ID must match the current user."""
    
    # Authorization Check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user.")

    # Delete User
    try:
        deleted = await user_service.delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except AttributeError:
        # Catch case if the method is not yet implemented in the service
        logger.error("AsyncUserService is missing the 'delete_user' method.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion service not fully implemented."
        )
    
    # Returns 204 No Content on success
    return None
