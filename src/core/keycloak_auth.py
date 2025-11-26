"""
Keycloak JWT Authentication & Authorization for POS System
Validates tokens from kc-pos-realm-dev and enforces RBAC.
"""
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError
from src.core.config import get_settings
from src.db.models import UserModel

logger = logging.getLogger(__name__)
settings = get_settings()

# Security scheme for Swagger UI
security = HTTPBearer()

# Cache for JWKS (JSON Web Key Set)
_jwks_cache: Optional[dict] = None


async def get_jwks() -> dict:
    """
    Fetch JWKS (public keys) from Keycloak for token verification.
    Caches the result to avoid repeated calls.
    """
    global _jwks_cache

    if _jwks_cache:
        return _jwks_cache

    try:
        # POS realm JWKS endpoint
        jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/kc-pos-realm-dev/protocol/openid-connect/certs"

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            _jwks_cache = response.json()
            logger.info("✅ JWKS fetched and cached from Keycloak")
            return _jwks_cache

    except Exception as e:
        logger.error(f"Failed to fetch JWKS from Keycloak: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from Keycloak and return decoded payload.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        dict: Decoded JWT payload with user info and roles

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Get JWKS for signature verification
        jwks = await get_jwks()

        # Decode and verify token
        # Keycloak tokens are signed with RS256 algorithm
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="account",  # Keycloak default audience
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_exp": True
            }
        )

        logger.debug(f"Token verified for user: {payload.get('preferred_username')}")
        return payload

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_roles(token_payload: dict) -> List[str]:
    """
    Extract realm roles from Keycloak token payload.

    Keycloak v24 structure:
    {
        "realm_access": {
            "roles": ["💰️ pos-cashier", "default-roles-kc-pos-realm-dev"]
        },
        "resource_access": {...}
    }

    Args:
        token_payload: Decoded JWT payload

    Returns:
        List of role names (including emoji prefixes)
    """
    realm_access = token_payload.get("realm_access", {})
    roles = realm_access.get("roles", [])

    # Filter out default roles, keep only POS roles
    pos_roles = [r for r in roles if "pos-" in r or r in ["💰️ pos-cashier", "👔️ pos-manager", "🛠️ pos-developer", "📊️ pos-auditor", "👑️ pos-admin"]]

    return pos_roles


def require_roles(allowed_roles: List[str]):
    """
    Decorator factory for role-based access control (RBAC).

    Usage:
        @router.post("/products")
        async def create_product(
            current_user: dict = Depends(require_roles(["💰️ pos-manager", "🛠️ pos-developer"]))
        ):
            # Only managers and developers can create products
            pass

    Args:
        allowed_roles: List of role names that are permitted access

    Returns:
        FastAPI dependency that validates user has required role
    """
    async def role_checker(token_payload: dict = Depends(verify_token)) -> dict:
        """
        Check if user has at least one of the required roles.

        Args:
            token_payload: Validated JWT payload from verify_token()

        Returns:
            dict: Token payload (passed through for endpoint use)

        Raises:
            HTTPException: 403 if user lacks required roles
        """
        user_roles = extract_roles(token_payload)
        username = token_payload.get("preferred_username", "unknown")

        # Check if user has ANY of the allowed roles
        has_permission = any(role in user_roles for role in allowed_roles)

        if not has_permission:
            logger.warning(
                f"Access denied for user '{username}'. "
                f"Required roles: {allowed_roles}, User roles: {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )

        logger.debug(f"Access granted for user '{username}' with roles: {user_roles}")

        # Add user info to payload for convenience
        token_payload["user_roles"] = user_roles
        token_payload["username"] = username

        return token_payload

    return role_checker


def require_any_pos_role():
    """
    Convenience decorator for endpoints that require ANY POS role.
    Use this for general authenticated POS endpoints.
    """
    return require_roles([
        "💰️ pos-cashier",
        "👔️ pos-manager",
        "🛠️ pos-developer",
        "📊️ pos-auditor",
        "👑️ pos-admin"
    ])


def require_admin():
    """
    Convenience decorator for admin-only endpoints.
    """
    return require_roles(["👑️ pos-admin"])


def require_manager_or_admin():
    """
    Convenience decorator for manager/admin endpoints.
    """
    return require_roles(["👔️ pos-manager", "👑️ pos-admin"])


# ================================================================
# Helper: Get current user from database (optional)
# ================================================================

async def get_current_user_from_token(
    token_payload: dict = Depends(verify_token),
    db = None  # Inject AsyncSession if needed
) -> Optional[UserModel]:
    """
    Fetch UserModel from database based on token username.

    Note: This is optional - you can work directly with token_payload
    if you don't need full UserModel object.

    Args:
        token_payload: Validated JWT payload
        db: Database session (optional)

    Returns:
        UserModel or None
    """
    username = token_payload.get("preferred_username")

    if not db:
        # If no DB session, return a minimal user dict
        return {
            "username": username,
            "email": token_payload.get("email"),
            "roles": extract_roles(token_payload)
        }

    # TODO: Query database for UserModel by username
    # from sqlalchemy import select
    # result = await db.execute(select(UserModel).where(UserModel.username == username))
    # return result.scalar_one_or_none()

    return None
