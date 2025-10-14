"""
API Router for handling user authentication. 
This router manages the login process and token generation.
It uses Dependency Injection (DI) to provide the AuthService instance.
"""
from datetime import timedelta
from typing import Any, List, Optional
import uuid # ⬅️ Added for typing if user.id is a UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

# --- ⚙️ Core/Database/Security Imports ---
from app.db.database import get_db_session 
from app.core.config import settings 
# 🔑 We MUST import the function that creates the token string
from app.core.security import create_access_token 

# --- 🛠️ Service Layer Import ---
# The AuthService handles database lookups and password verification (business logic)
from app.services.auth_service import AuthService
from app.db.models.user_model import User # Used for type hinting

# -----------------------------------------------------------------------------
# 🚀 Router Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

auth_router = APIRouter(
    prefix="/auth",
    tags=["🐘️ Authentication"],
)

# -----------------------------------------------------------------------------
# 🔗 Dependency Injector for AuthService
# -----------------------------------------------------------------------------
def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    DI helper: Creates and returns an AuthService instance linked to the current DB session.
    """
    logger.debug("Injecting AuthService with current DB session.")
    return AuthService(db)

# -----------------------------------------------------------------------------
# 🚪 The /token Endpoint (Login)
# -----------------------------------------------------------------------------
@auth_router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return JWT access token",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Handles user login using standard username (email) and password. 
    Returns a JWT access token if credentials are valid.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # 1. Authenticate the user 🕵️‍♂️
    # The service layer validates the password and returns the User model if successful.
    user: Optional[User] = await auth_service.authenticate_user(
        email=form_data.username, 
        password=form_data.password
    )

    if not user:
        # ❌ Failure: Incorrect credentials
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 🚫 Failure: User is disabled
        logger.warning(f"Attempt to login with inactive account: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive or disabled"
        )

    # 2. Define token expiry and create the token 🥇
    
    # Define how long the token is valid for
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # --- 💥 CRITICAL FIX HERE! 💥 ---
    # The 'create_access_token' function (in app/core/security.py) requires 
    # the keyword arguments 'subject' and 'scopes', not 'data'.
    
    # Subject: The unique ID used to identify the user later (MUST be a string/UUID).
    subject_id: Union[str, uuid.UUID] = user.id
    
    # Scopes: The user's permissions/roles (MUST be a list of strings).
    # Assuming your User model has a 'roles' attribute (List[str]).
    # Fallback to ["basic"] if user.roles is not set.
    user_scopes: List[str] = user.roles if hasattr(user, 'roles') and user.roles else ["basic"]

    access_token = create_access_token(
        # ✅ Correct Argument: subject=
        subject=subject_id, 
        
        # ✅ Correct Argument: scopes=
        scopes=user_scopes, 
        
        # ✅ Correct Argument: expires_delta=
        expires_delta=access_token_expires,
    )
    # ---------------------------------
    
    logger.info(f"✅ Successful login and token creation for user: {user.email}")
    
    # 3. Return the standard OAuth2 token response 🎁
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

# NOTE ON NAMES:
# I maintained all names (auth_router, login_for_access_token, AuthService, etc.)
# The only change was in step 2 (the CRITICAL FIX) where the call to 
# create_access_token was changed from:
#     data={...} 
# to:
#     subject=user.id, scopes=user_roles 
# This alignment is mandatory for the Python code to execute without a TypeError.
