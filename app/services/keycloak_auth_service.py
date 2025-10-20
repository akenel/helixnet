import httpx
import logging
from typing import Dict, Any, List
from functools import lru_cache

from jose import jwt, jws
from jose.exceptions import JWTError, JWTClaimsError

from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache for the Keycloak JWKS keys
# The keys rarely change, so caching them drastically improves performance.
@lru_cache(maxsize=1)
def get_keycloak_jwks() -> List[Dict[str, Any]]:
    """
    Fetches the JSON Web Key Set (JWKS) from Keycloak. 
    This function is cached to prevent repeated network calls.
    """
    try:
        # Use synchronous httpx.get for the initial cached startup fetch
        response = httpx.get(settings.KEYCLOAK_JWKS_URL, timeout=10)
        response.raise_for_status()
        jwks = response.json().get('keys', [])
        
        if not jwks:
            logger.error("Keycloak JWKS endpoint returned no keys.")
            raise RuntimeError("Could not retrieve public keys for token validation.")
        
        logger.info(f"Successfully fetched {len(jwks)} Keycloak public keys from {settings.KEYCLOAK_JWKS_URL}")
        return jwks
        
    except (httpx.RequestError, httpx.HTTPStatusError, RuntimeError) as e:
        # We raise a critical error if keys cannot be fetched on startup
        logger.critical(f"FATAL: Failed to fetch Keycloak JWKS from {settings.KEYCLOAK_JWKS_URL}. Is Keycloak running? Error: {e}")
        # In a real startup sequence, this should crash the app until keycloak is ready.
        # For a FastAPI dependency, we raise an HTTP 503 error if called later.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication server (Keycloak) keys are unavailable."
        )

class KeycloakAuthService:
    """
    Service responsible for validating JWTs against the Keycloak JWKS.
    """
    def __init__(self):
        self.jwks = get_keycloak_jwks()
        self.issuer = settings.KEYCLOAK_ISSUER_URL
        self.audience = settings.KEYCLOAK_CLIENT_ID
        self.algorithm = settings.KEYCLOAK_ALGORITHM # RS256

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validates the JWT signature, claims, and returns the decoded payload.
        """
        try:
            # 1. Decode and Verify the token using the fetched public keys
            payload = jwt.decode(
                token,
                key=self.jwks,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    # Enforce critical claims verification
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                }
            )
            return payload

        except JWTClaimsError as e:
            logger.warning(f"JWT Claims Validation Failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token claims failed: {e}"
            )
        except JWTError as e:
            logger.warning(f"JWT Signature or Decoding Failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token signature: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not validate token due to internal service error."
            )
