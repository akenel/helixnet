import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db_session
from app.models.user_model import User
from app.schemas.token_schema import TokenData
from app.services.user_service import get_user_by_email, get_user_by_id

# --- Configuration ---
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

# 🔑 The scheme instance that powers the Swagger UI 'Authorize' button
# The tokenUrl must match the actual endpoint where the token is issued.
# NOTE: The dependency's name in the OpenAPI schema is often derived from the variable name,
# or set explicitly using scheme_name. We rely on the standard default behavior here.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

# --- Password Hashing Utilities ---


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password."""
    return pwd_context.hash(password)


# --- JWT Encoding/Decoding ---


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decodes a JWT access token and returns the payload data."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_email: str | None = payload.get("sub")

        if user_email is None:
            raise credentials_exception

        token_data = TokenData(email=user_email)
        return token_data

    except JWTError:
        logger.warning("JWT decoding failed.")
        raise credentials_exception


# --- FastAPI Dependencies ---


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    token: Annotated[
        str, Depends(oauth2_scheme)
    ],  # <--- Dependency on the scheme instance
) -> User:
    """
    Dependency function to get the currently authenticated user based on the JWT token.
    """
    token_data = decode_access_token(token)
    user = await get_user_by_email(db, email=token_data.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency function that ensures the authenticated user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_active_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency function that ensures the authenticated user is an active admin.
    """
    # NOTE: You will need to implement an 'is_admin' field or a role system in the User model
    # to make this check fully functional. For now, it defaults to checking if the email
    # matches the initial admin defined in the settings.
    if current_user.email != settings.FIRST_SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges",
        )
    return current_user
