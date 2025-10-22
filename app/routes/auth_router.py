"""
API Router for handling user authentication (Login/Token Generation).
This router uses Dependency Injection (DI) to provide the AuthService instance.
"""
from datetime import timedelta
from typing import Any, List, Optional, Union
import uuid
import logging

from app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

# --- ⚙️ Core/Database/Security Imports ---
from app.db.database import get_db_session 
from app.core.config import settings
# from app.core.security import  create_access_token
from app.services.auth_service import get_auth_service, AuthService
from app.schemas.token_schema import TokenResponse 
from app.db.models.user_model import UserModel
from app.services.keycloak_auth_service import get_keycloak_jwks
# -----------------------------------------------------------------------------
# 🚀 Router Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
# ⬅️ CRITICAL FIX: Adding prefix="/auth" to resolve the 404 routing conflict
# IMPORTANT: The APIRouter instance MUST be named 'auth_router'
# for 'from .auth_router import auth_router' to work correctly.
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@auth_router.post("/login")
async def login_user():
    """Placeholder for user login logic."""
    return {"message": "Login successful (Placeholder)"}

@auth_router.post("/refresh")
async def refresh_token():
    """Placeholder for token refresh logic."""
    return {"message": "Token refreshed (Placeholder)"}

# -----------------------------------------------------------------------------
# 🚪 The /token Endpoint (Login)
# -----------------------------------------------------------------------------
@auth_router.post(
    "/auth/token",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Authenticate user and return JWT access and refresh tokens",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """
    Handles user login using standard username (email) and password. 
    Returns a JWT access token and a refresh token if credentials are valid.
    """
    logger.info(f"[AUTH] Login attempt initiated for user: {form_data.username}")
    
    # 1. Authenticate the user 🕵️‍♂️
    user: Optional[UserModel] = await auth_service.authenticate_user(
        email=form_data.username, 
        password=form_data.password
    )

    if not user:
        # ❌ Failure: Incorrect credentials
        logger.warning(f"[AUTH] Failed login (Incorrect credentials) for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # 🚫 Failure: User is disabled
        logger.warning(f"[AUTH] Attempt to login with inactive account: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive or disabled"
        )

    # 2. Prepare for token generation 🥇
    subject_id: str = str(user.id) 
    user_scopes: List[str] = user.roles if hasattr(user, 'roles') and user.roles else ["basic"]
    
    logger.debug(f"[AUTH] User authenticated. Subject ID: {subject_id}, Scopes: {user_scopes}")

    # 3. Create Access Token (Short-lived)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = get_keycloak_jwks(
        data={UserModel},
        expires_delta=access_token_expires,
    )
    logger.debug(f"[AUTH] Access token created, expires in {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes.")


    # 4. Create Refresh Token (Long-lived)
    # NOTE: Assumed setting REFRESH_TOKEN_EXPIRE_MINUTES exists in app.core.config.settings
    # 💥 CRITICAL FIX: Assumed create_refresh_token returns a dictionary {'token': 'string'}
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS_PRO) 
    token_response_data = get_keycloak_jwks(
        expires_delta=refresh_token_expires,
    )
    
    # Pydantic Error Fix: Safely extract the token string from the dictionary.
    refresh_token_string: Optional[str] = token_response_data.get('token')
    
    if not refresh_token_string:
        logger.error(f"[AUTH] 🚨 Internal Error: Failed to extract 'token' string from refresh token function output: {token_response_data}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal token generation error. See logs for details."
        )

    logger.debug(f"[AUTH] Refresh token created, expires in {settings.REFRESH_TOKEN_EXPIRE_DAYS_PRO} minutes.")
    
    # 5. Return the full TokenResponse 🎁
    logger.info(f"✅ [AUTH] Successful login and token issuance for user: {user.email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_string, # Use the extracted string
        token_type="bearer"
    )
