import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.auth import (
    TokenRequest, 
    RefreshTokenRequest, 
    KeycloakTokenResponse
)
from app.services.keycloak_proxy_service import KeycloakProxyService

logger = logging.getLogger(__name__)
auth_router = APIRouter()

# Dependency function to provide the KeycloakProxyService
async def get_keycloak_proxy_service():
    """Dependency that yields a KeycloakProxyService instance."""
    service = KeycloakProxyService()
    try:
        yield service
    finally:
        # Ensure the httpx client is closed when the request is done
        await service.close()

# Alias for type annotation clarity
KeycloakService = Annotated[KeycloakProxyService, Depends(get_keycloak_proxy_service)]


@auth_router.post(
    "/token", 
    response_model=KeycloakTokenResponse, 
    summary="Exchange credentials for Access and Refresh Tokens via Keycloak"
)
async def login_for_tokens(
    request: Request,
    response: Response,
    form_data: TokenRequest,
    keycloak_service: KeycloakService,
):
    """
    Proxies the username and password to Keycloak's token endpoint and handles
    the successful token response, setting the refresh token as an HttpOnly cookie.
    """
    logger.info(f"Attempting login for user: {form_data.username}")

    # 1. Exchange Credentials for Tokens via Keycloak Service
    tokens = await keycloak_service.get_initial_tokens(
        username=form_data.username, 
        password=form_data.password
    )

    # 2. Set the Refresh Token as an HttpOnly Cookie (Security Best Practice)
    # The access token is returned in the response body for the client to use immediately.
    if settings.USE_HTTP_ONLY_REFRESH_COOKIE:
        response.set_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            value=tokens.refresh_token,
            # Max age is determined by the Keycloak refresh token validity
            max_age=3600 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT, # Use a generous max_age based on your Keycloak config
            expires=3600 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT,
            httponly=True,
            secure=request.url.scheme == "https", # Only set secure in production/https
            samesite="Lax"
        )
        # CRITICAL: We clear the refresh_token from the response body if it's set in a cookie
        tokens.refresh_token = "[HTTP-ONLY-COOKIE]" # Mask the value for security logging

    logger.info(f"Successful login and token retrieval for user: {form_data.username}")
    return tokens


@auth_router.post(
    "/refresh", 
    response_model=KeycloakTokenResponse,
    summary="Exchange Refresh Token for new Access Token pair"
)
async def refresh_tokens(
    request: Request,
    response: Response,
    keycloak_service: KeycloakService,
):
    """
    Uses the refresh token (expected in HttpOnly cookie or body) to get a new
    Access Token and Refresh Token pair from Keycloak.
    """
    refresh_token = None
    
    # 1. Attempt to extract refresh token from HttpOnly cookie
    if settings.USE_HTTP_ONLY_REFRESH_COOKIE:
        refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    
    # 2. Handle missing token
    if not refresh_token:
        # If the token is not in the cookie, it must be provided in the request body (e.g., from a client-side implementation)
        # Note: You might want to implement a Pydantic body parser here if you support both cookie and body.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from cookie or body. Please re-authenticate."
        )

    logger.info("Attempting token refresh.")
    
    # 3. Exchange Refresh Token via Keycloak Service
    tokens = await keycloak_service.refresh_access_token(refresh_token=refresh_token)
    
    # 4. Update the HttpOnly Refresh Token Cookie with the new token
    if settings.USE_HTTP_ONLY_REFRESH_COOKIE:
        response.set_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            value=tokens.refresh_token,
            max_age=3600 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT,
            expires=3600 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="Lax"
        )
        tokens.refresh_token = "[HTTP-ONLY-COOKIE]"

    logger.info("Token refresh successful.")
    return tokens
