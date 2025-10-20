import logging
from typing import Annotated, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# 🥋 Keycloak Validation Logic lives here 🥋
# This service fetches the public keys (JWKS) from Keycloak and validates the token.
from app.services.keycloak_auth_service import KeycloakAuthService 

logger = logging.getLogger("app/core/security.py")

# --- TEMPORARY STUB: To Fix Immediate ImportError in user_service.py ---
def get_password_hash(password: str) -> str:
    """
    ⚠️ TEMPORARY STUB: This function is required by an old import in user_service.py 
    that attempts to create initial users.
    
    When using Keycloak, your application should **NOT** be hashing passwords locally. 
    Passwords are managed externally. This function MUST be removed along with its 
    imports in app/services/user_service.py once that file is refactored.
    """
    logger.warning("⚠️ Using temporary stub for get_password_hash. Refactor user_service.py immediately!")
    # Return a dummy string to allow user_service to initialize
    return "KEYCLOAK_MANAGED_HASH_STUB"
# -------------------------------------------------------------------


# --- 🥊 KEYCLOAK VALIDATION DEPENDENCY 🥊 ---

# 1. OAuth2PasswordBearer: Tells FastAPI to look for a 'Bearer <token>' in the Authorization header.
#    The tokenUrl points to your custom FastAPI endpoint that handles the login/token exchange.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """
    FastAPI Dependency: The core of the Keycloak roundhouse kick!
    It validates the Bearer token signature, expiry, issuer, and audience against
    Keycloak's public keys (fetched via KEYCLOAK_JWKS_URL defined in settings).

    Returns: The decoded JWT payload (e.g., {'sub': 'user-uuid', 'roles': [...]}).
    Raises: HTTPException 401/403 if the token is invalid or missing.
    """
    if token == "[HTTP-ONLY-COOKIE]":
        # 🚨 Security Note: Prevents HttpOnly refresh tokens from being used for resource access.
        logger.warning("Attempted to use Http-Only refresh token for protected resource access.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only access tokens can access secured endpoints."
        )

    try:
        # Initialize the service (it uses cached Keycloak keys)
        auth_service = KeycloakAuthService()
        
        # Validate the token using the remote public keys
        payload = auth_service.validate_token(token)
        
        logger.debug(f"Token successfully verified for user SUB: {payload.get('sub')}")
        return payload
    
    except HTTPException as e:
        # Re-raise explicit HTTP exceptions from the validation service (e.g., 401 Unauthorized)
        raise e
    except Exception as e:
        # Catch unexpected errors during dependency execution
        logger.error(f"Unexpected token dependency failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token processing failed due to internal service error."
        )
        
# 🌟 Primary Dependency Alias: Use this in all your protected routes.
ActiveUserPayload = Annotated[Dict[str, Any], Depends(get_current_user)]
