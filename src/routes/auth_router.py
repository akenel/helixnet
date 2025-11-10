# src/routes/auth_router.py
"""
Authentication Router for handling login and token refresh.
"""

from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm

from src.schemas.token_schema import TokenResponse
 
# from src.services.auth_service import KeycloakAuthService, get_auth_service
from src.services.keycloak_service import KeycloakProxyService, get_keycloak_proxy
logger = logging.getLogger("routes.auth_router")

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# =========================================================
# 🔐 Login Endpoint (Local Auth)
# =========================================================
@auth_router.post(
    "/token",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Authenticate user and return JWT access and refresh tokens",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: KeycloakProxyService = Depends(get_keycloak_proxy),
) -> Any:
    """
    Authenticates the user against the local DB and issues JWT access + refresh tokens.
    """
    email = form_data.username
    password = form_data.password

    logger.info(f"[AUTH] Login attempt for user: {email}")

    # 🔹 Step 1: Check user credentials against DB
    user = await auth_service.authenticate_user(email, password)
    if not user:
        logger.warning(f"[AUTH] Invalid credentials for user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 🔹 Step 2: Issue token pair (access + refresh)
    token_pair = await auth_service.create_token_pair_for_user(user)

    logger.info(f"✅ [AUTH] Tokens issued for {email}")
    return TokenResponse(**token_pair)


# =========================================================
# ♻️ Refresh Token Endpoint
# =========================================================
@auth_router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Refresh access token using a valid refresh token",
)
async def refresh_token(
    refresh_token: str = Form(...),
    auth_service: KeycloakProxyService = Depends(get_keycloak_proxy),
):
    """
    Validates and rotates a refresh token to issue a new access/refresh pair.
    """
    new_tokens = await auth_service.verify_and_refresh_token_pair(refresh_token)

    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("[AUTH] Access token refreshed successfully.")
    return TokenResponse(**new_tokens)
