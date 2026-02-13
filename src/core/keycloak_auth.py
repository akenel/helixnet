"""
Keycloak JWT Authentication & Authorization - Multi-Realm
Validates tokens from any Keycloak realm by reading the issuer (iss) claim.
Supports POS, Camper & Tour, and any future realm.
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


# Cache for multiple realms
_jwks_cache_by_realm: dict = {}

# POS realm - hardcoded because POS frontend uses this specific realm
POS_REALM = "kc-pos-realm-dev"


async def get_jwks(realm: str = None) -> dict:
    """
    Fetch JWKS (public keys) from Keycloak for token verification.
    Caches the result per realm to avoid repeated calls.

    Args:
        realm: The realm to fetch JWKS from. Defaults to POS_REALM for POS routes.
    """
    global _jwks_cache_by_realm

    realm = realm or POS_REALM

    if realm in _jwks_cache_by_realm:
        return _jwks_cache_by_realm[realm]

    try:
        # Fetch JWKS from the specified realm
        jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{realm}/protocol/openid-connect/certs"

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            _jwks_cache_by_realm[realm] = response.json()
            logger.info(f"✅ JWKS fetched and cached from Keycloak realm: {realm}")
            return _jwks_cache_by_realm[realm]

    except Exception as e:
        logger.error(f"Failed to fetch JWKS from Keycloak realm {realm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


def _extract_realm_from_token(token: str) -> str:
    """
    Extract the realm name from a JWT token's issuer (iss) claim
    WITHOUT verifying the signature first (we need the realm to fetch
    the right JWKS to verify the signature -- chicken-and-egg).

    Keycloak iss format: https://keycloak.helix.local/realms/{realm-name}

    Returns realm name, or falls back to POS_REALM if extraction fails.
    """
    try:
        # Decode without verification just to read the iss claim
        unverified = jwt.get_unverified_claims(token)
        issuer = unverified.get("iss", "")

        # Extract realm from issuer URL: .../realms/{realm-name}
        if "/realms/" in issuer:
            realm = issuer.split("/realms/")[-1].rstrip("/")
            if realm:
                return realm

        logger.warning(f"Could not extract realm from iss: {issuer}, falling back to {POS_REALM}")
        return POS_REALM

    except Exception as e:
        logger.warning(f"Failed to read token claims for realm extraction: {e}")
        return POS_REALM


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from any Keycloak realm and return decoded payload.

    Multi-realm flow:
    1. Read the token's iss claim (unverified) to determine the realm
    2. Fetch JWKS for that specific realm
    3. Verify signature + expiry against the correct keys

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        dict: Decoded JWT payload with user info and roles

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Step 1: Extract realm from token's iss claim
        realm = _extract_realm_from_token(token)

        # Step 2: Get JWKS for the correct realm
        jwks = await get_jwks(realm=realm)

        # Step 3: Decode and verify token with realm-specific keys
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,  # Skip audience check - Keycloak public clients may not have audience
                "verify_exp": True
            }
        )

        logger.debug(f"Token verified for user: {payload.get('preferred_username')} (realm: {realm})")
        return payload

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions from get_jwks (503)
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

    Multi-realm aware: returns ALL application roles (pos-*, camper-*, etc.)
    Filters out Keycloak default roles (default-roles-*, uma_authorization, offline_access).

    Keycloak v24 structure:
    {
        "realm_access": {
            "roles": ["camper-mechanic", "default-roles-kc-camper-service-realm-dev"]
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

    # Known application role prefixes across all realms
    app_prefixes = ("pos-", "camper-", "isotto-")

    # Keep any role that matches an app prefix (plain or emoji-prefixed)
    app_roles = [r for r in roles if any(prefix in r for prefix in app_prefixes)]

    return app_roles


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
        # Handles both emoji-prefixed roles ("💰️ pos-cashier") and plain roles ("pos-cashier")
        # by checking if the allowed_role string is contained in any user_role
        def role_matches(allowed_role: str, user_role: str) -> bool:
            """Check if allowed_role matches user_role (handles emoji prefixes)"""
            # Exact match
            if allowed_role == user_role:
                return True
            # allowed_role is substring of user_role (e.g., "pos-admin" in "👑️ pos-admin")
            if allowed_role in user_role:
                return True
            # user_role is substring of allowed_role (e.g., "👑️ pos-admin" contains "pos-admin")
            if user_role in allowed_role:
                return True
            return False

        has_permission = any(
            role_matches(allowed_role, user_role)
            for allowed_role in allowed_roles
            for user_role in user_roles
        )

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
        "pos-cashier",
        "pos-manager",
        "pos-developer",
        "pos-auditor",
        "pos-admin"
    ])


def require_admin():
    """
    Convenience decorator for admin-only endpoints.
    """
    return require_roles(["pos-admin"])


def require_manager_or_admin():
    """
    Convenience decorator for manager/admin endpoints.
    """
    return require_roles(["pos-manager", "pos-admin"])


# ================================================================
# Camper & Tour Role Helpers (Sebastino's Shop)
# ================================================================

def require_any_camper_role():
    """Any authenticated Camper & Tour staff."""
    return require_roles([
        "camper-counter",
        "camper-mechanic",
        "camper-manager",
        "camper-admin",
        "camper-auditor",
        "camper-hr",
        "camper-accountant",
    ])


def require_camper_mechanic_or_above():
    """Mechanic, manager, or admin at Camper & Tour."""
    return require_roles([
        "camper-mechanic",
        "camper-manager",
        "camper-admin",
    ])


def require_camper_manager_or_admin():
    """Manager or admin only at Camper & Tour."""
    return require_roles([
        "camper-manager",
        "camper-admin",
    ])


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
