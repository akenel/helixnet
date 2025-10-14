"""
Authentication and Authorization Dependencies for FastAPI.
These functions handle token validation, user retrieval, and scope enforcement.
"""

import uuid
from typing import Annotated, List
import logging

from fastapi.security import SecurityScopes
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import  JWTError

# --- Project Imports ---
from app.db.database import get_db_session
from app.db.models.user_model import User
from app.core.security import decode_token, oauth2_scheme
from app.services.user_service import UserService

# Initialize the logger
logger = logging.getLogger(__name__)

# Initialize the user service
user_service = UserService()

async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    🔑 Dependency: Validate JWT access token, fetch user from DB, and enforce scopes.
    
    Args:
        security_scopes (SecurityScopes): The required security scopes.
        db (AsyncSession): The database session.
        token (str): The OAuth2 access token.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If the credentials are invalid or insufficient scopes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
    )

    # 1. Decode & validate token
    try:
        payload = decode_token(token)
        logger.info("Token decoded successfully.")
    except JWTError as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

    # 2. Check token type (must be 'access')
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning("Invalid token type: %s", token_type)
        raise credentials_exception

    # 3. Extract user ID and token scopes
    user_id_str = payload.get("sub")
    token_scopes: List[str] = payload.get("scopes", [])
    
    # 4. Validate user ID format
    try:
        if not user_id_str:
            logger.warning("User ID is missing from the token.")
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
        logger.info("User ID validated: %s", user_id)
    except (ValueError, TypeError) as exc:
        logger.error(f"Invalid user ID format: {exc}")
        raise credentials_exception
    
    # 5. Fetch user from DB
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        logger.warning("User not found: %s", user_id)
        raise credentials_exception

    # 6. Active user check
    if not user.is_active:
        logger.warning("User is inactive: %s", user_id)
        raise credentials_exception

    # 7. Scope checks
    missing_scopes = [scope for scope in security_scopes.scopes if scope not in token_scopes]
    if missing_scopes:
        logger.error("Not enough permissions: Missing required scopes: %s", missing_scopes)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions: Missing required scopes: {missing_scopes}",
        )

    logger.info("User %s authenticated successfully with scopes: %s", user_id, token_scopes)
    return user

async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Ensures the current active user has admin privileges.
    
    Args:
        user (User): The authenticated user object.

    Returns:
        User: The authenticated admin user object.

    Raises:
        HTTPException: If the user does not have admin privileges.
    """
    if not user.is_admin:  # Check if the user has admin privileges
        logger.warning("Permission denied for user %s. Requires admin privileges.", user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Requires admin privileges."
        )
    
    logger.info("User %s is an admin.", user.id)
    return user

# Docker Information Logs
logger.info("FastAPI application is running inside a Docker container.")