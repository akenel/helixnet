import logging
from app.db.models import User
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.db.database import get_db_session
from app.services import user_service
from datetime import timedelta
from typing import Dict, Any
from app.core.config import settings
##################################################################################################
# 🔑 NECESSARY IMPORTS from the cleaned-up security file!
from app.core.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    # Removed stub import since we use the service layer
)

##################################################################################################
logger = logging.getLogger(__name__)
##################################################################################################
# --- ROUTER SETUP ---
# CRITICAL FIX: Renaming to 'router' to match import in app/main.py
auth_router = APIRouter()


##################################################################################################
def require_roles(*roles):
    async def _require_roles(current_user=Depends(user_service.get_current_user)):
        user_roles = getattr(current_user, "roles", [])
        if not any(r in user_roles for r in roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return _require_roles


# Example : @router.post("/tasks", dependencies=[Depends(require_roles("user"))])
#           async def create_task(...):
##################################################################################################
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

    # 1. Verify user credentials using the ASYNCHRONOUS service layer function
    # user_data is expected to be a User ORM object if successful
    user_data: User | None = await user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user_data:
        logger.debug(f"[AUTH_ROUTE] ❌ Authentication FAILED for {form_data.username}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 🔑 FIX 1: Access the ID using DOT NOTATION (.id) because user_data is a User object.
    # 🔑 FIX 2: Convert the UUID object to a STRING using str() for the JWT subject.
# 🔑 FIX: Retrieve the dynamic scope list from the authentication service payload
    access_token = create_access_token(
        subject=user_data["sub"],
        scopes=user_data["scopes"],  # ✅ CORRECT: Now includes 'admin' if applicable
    )

    # 3. Return the token in the required OAuth2 format
# 3. Return the token in the required OAuth2 format
    logger.debug(
        f"[AUTH_ROUTE] ✅ Authentication SUCCESSFUL for {form_data.username}. Generating token."
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        # 🎯 FIX: Use the imported constant * 60 seconds.
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
    }

##################################################################################################
@auth_router.get("/admin-only")
async def admin_only_route(
    current_user=Security(user_service.get_current_user, scopes=["admin"])
):
    """
    Authenticates the user and returns the JWT access token.
    """
    # NOTE: The original log message had a typo (format.username), corrected to use current_user's email if needed
    logger.debug(
        f"[AUTH_ROUTE] 🔍 Current user attempting admin access: {getattr(current_user, 'email', 'N/A')}"
    )
    return {"msg": "Helix 🐘️ Admin"}
