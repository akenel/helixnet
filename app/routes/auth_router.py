# app/routes/auth_router.py
import logging
import uuid
from fastapi import Body
from jose import JWTError, ExpiredSignatureError

from app.db.models import User
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.services import user_service
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db_session
from app.services.user_service import authenticate_user, get_user_by_id

# Check DB for jti and not revoked and not expired
from app.schemas.user_schema import TokenPairOut

# Load user ################################################################
from app.services.user_service import get_user_by_id

##################################################################################################
from app.core.security import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    decode_token,
    # Removed stub import since we use the service layer
)

##################################################################################################
logger = logging.getLogger("app/routes/auth_router.py")
auth_router = APIRouter()


##################################################################################################
def require_roles(*roles):
    async def _require_roles(current_user=Depends(user_service.get_current_user)):
        user_roles = getattr(current_user, "roles", [])
        if not any(r in user_roles for r in roles):
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return _require_roles


##################################################################################################
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

    # 1. 🔑 Verify user credentials using the ASYNCHRONOUS service layer function
    # user_data is expected to be a User ORM object if successful
    # Access the ID using DOT NOTATION (.id) because user_data is a User object.
    # Convert the UUID object to a STRING using str() for the JWT subject.
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

    # 🔑 2. Retrieve the dynamic scope list from the authentication service payload
    access_token = create_access_token(
        subject=user_data["sub"],
        scopes=user_data["scopes"],  # ✅ CORRECT: Now includes 'admin' if applicable
    )

    # 3. Return the token in the required OAuth2 format
    logger.debug(
        f"[AUTH_ROUTE] ✅ Authentication SUCCESSFUL for {form_data.username}. Generating token."
    )
    # 🎯 4. Use the imported constant * 60 seconds.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "🎯 the Bearer / access_token": access_token,
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

    logger.debug(
        f"[AUTH_ROUTE] 🔍 Current user attempting admin access: {getattr(current_user, 'email', 'N/A')}"
    )
    return {"msg": "Helix 🐘️ Admin"}


##################################################################################################


@auth_router.post("/login", response_model=TokenPairOut)
async def login_for_access_token(
    form_data: dict,
    db: AsyncSession = Depends(get_db_session),
    response: Response = None,
):
    """
    Example expects form_data with 'username' and 'password' (adapt to your auth flow).
    """
    username = form_data.get("username")
    password = form_data.get("password")
    user = await authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials"
        )
    scopes = ["user"]
    if user.is_admin:
        scopes.append("admin")
    if getattr(user, "is_pro", False):
        scopes.append("pro")
    tokens = await create_token_pair_for_user(db, user, scopes)
    return tokens


##################################################################################################
@auth_router.post("/logout", status_code=204)
async def logout(
    refresh_token: str = Body(...), db: AsyncSession = Depends(get_db_session)
):
    from app.services.auth_service import revoke_refresh_jti

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    jti = payload.get("jti")
    if jti:
        await revoke_refresh_jti(db, jti)
    return Response(status_code=204)


##################################################################################################
@auth_router.post("/token/refresh", response_model=TokenPairOut)
async def refresh_token_endpoint(
    refresh_token: str = Body(..., embed=True),  # or read from cookie
    db: AsyncSession = Depends(get_db_session),
):

    try:
        payload = decode_token(refresh_token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti or not sub:
        raise HTTPException(status_code=401, detail="Malformed token")

    rt = await get_refresh_record(db, jti)
    if not rt or rt.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or unknown")
    if rt.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired (DB)")

    # Rotate: revoke old #######################################################
    await revoke_refresh_jti(db, jti)
    user = await get_user_by_id(db, uuid.UUID(sub))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    scopes = ["user"]
    if user.is_admin:
        scopes.append("admin")
    if getattr(user, "is_pro", False):
        scopes.append("pro")

    tokens = await create_token_pair_for_user(db, user, scopes)
    return tokens
