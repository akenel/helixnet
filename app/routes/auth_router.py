import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.db.database import get_db_session
from app.services import user_service  # Your user service with hashing/auth logic
from datetime import timedelta
from typing import Dict, Any

# 🔑 NECESSARY IMPORTS from the cleaned-up security file!
from app.core.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    # Removed stub import since we use the service layer
)

logger = logging.getLogger(__name__)

# --- ROUTER SETUP ---
# CRITICAL FIX: Renaming to 'router' to match import in app/main.py
auth_router = APIRouter(tags=["🐘️ Authentication : auth_router"])


@auth_router.post(
    "/token",
    response_model=Dict[str, Any],
    summary="Login For Access Token",
    description="Handle user login via OAuth2 Password flow and return an access token.",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticates the user and returns the JWT access token.
    """
    logger.debug(f"[AUTH_ROUTE] 🔍 Attempting authentication for: {form_data.username}")

    # 1. CRITICAL FIX: Verify user credentials using the ASYNCHRONOUS service layer function
    user_data = await user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )

    if not user_data:
        logger.debug(f"[AUTH_ROUTE] ❌ Authentication FAILED for {form_data.username}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Create the JWT token
    # Use settings for consistency
    expire_minutes = getattr(
        Settings, "ACCESS_TOKEN_EXPIRE_MINUTES", ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token_expires = timedelta(minutes=expire_minutes)

    # 💡 user_data MUST contain the necessary payload fields (like 'id')
    access_token = create_access_token(
        data=user_data, expires_delta=access_token_expires
    )

    # 3. Return the token in the required OAuth2 format
    logger.debug(
        f"[AUTH_ROUTE] ✅ Authentication SUCCESSFUL for {form_data.username}. Generating token."
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expire_minutes * 60,
    }
