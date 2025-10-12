# --------------------------------------------------------------------
# 📦 CORE IMPORTS - The Single Source of Truth for Security
# --------------------------------------------------------------------
import logging
import uuid
from typing import Optional, Dict, Any, Union
from datetime import (
    datetime,
    timedelta,
    timezone,
)  # 💡 Use timezone.utc for time consistency
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext  # 🔑 Hashing library
from jose import jwt, JWTError  # 🔐 JWT handling
from pydantic import BaseModel, Field

logger = logging.getLogger("app/core/security.py")
# ⚙️ APPLICATION CORE IMPORTS
from app.core.config import settings  # 🌍 Get config settings

# 🔑 Hashing Context: Defines the scheme for password hashing # Only define this ONCE.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 🔒 JWT Configuration: Loaded from settings- -- CONFIGURATION & CONSTANTS ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


# 💡 Token Payload Schema (Data decoded from JWT)
class TokenData(BaseModel):
    """Token Data (email + scopes) Schema for the data extracted from a decoded JWT payload."""

    email: Optional[str] = Field(
        None,
        description="The subject (sub) of the token, typically user's email or ID.",
    )
    # 🎯 Include scopes in the expected data structure
    scopes: list[str] = []


# 🚪 OAuth2 Scheme: Defines the token endpoint and available scopes
# Only define this ONCE.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/token",
    scopes={
        "admin": "Admin privileges: full access to sensitive endpoints | edit_all",
        "user": "User secure privileges: general application access | edit_all",
        "dev": "Developer privileges : application access (no sudo) | edit_all",
        "audit": "Audit privileges: general application | view_only",
        "test": "Test privileges: general application | view_only",
        "guest": "Guest privileges: general application | view_only",
    },
)


# ====================================================================
# 🛡️ PASSWORD UTILITIES (The ONE place for hashing/verification)
# ====================================================================
def _now():
    return datetime.now(timezone.utc)


###################################################################################


def get_password_hash(password: str) -> str:
    """
    🔒 Generates a secure hash for a given password using CryptContext.
    """
    return pwd_context.hash(password)


###################################################################################
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    ✅ Checks if the plain password matches the hashed password using CryptContext.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ====================================================================
# 🔑 JWT UTILITIES (TOKEN CREATION & VALIDATION)
# ====================================================================
def create_access_token(
    subject: Union[str, Any],
    scopes: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a JWT access token for a given user subject and scopes.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # ⏳ Default expiry time if not provided, using UTC
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 📝 Data to be encoded in the token payload
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "scopes": scopes,  # Inject scopes directly into the token
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


###################################################################################
def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes a JWT token and returns the payload dictionary.
    Raises HTTPException on failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 🔐 Decode the token using the application's SECRET_KEY and ALGORITHM
        payload: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 🎯 Ensure required fields exist in the payload
        if payload.get("sub") is None or payload.get("scopes") is None:
            raise credentials_exception

        return payload

    except JWTError:
        logger.warning("💥 JWT decoding failed: Token invalid or expired.")
        raise credentials_exception


# ⚠️ NOTE: The dependency functions (get_current_active_user, get_current_active_admin_user,
# and the actual token extraction/DB lookup logic) should ideally live in your
# /app/services/user_service.py or /app/dependencies.py, as they tie security
# (the token) to business logic (the database User model).
###################################################################################


def create_access_token(
    *, subject: str, scopes: list[str], expires_delta: Optional[timedelta] = None
) -> str:
    now = _now()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


###################################################################################
def create_refresh_token(
    *, subject: str, expires_delta: Optional[timedelta] = None
) -> tuple[str, str, datetime]:
    """
    Returns (token, jti, expires_at)
    jti saved in DB for revocation/rotation.
    """
    now = _now()
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT))
    jti = str(uuid.uuid4())
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, expire


###################################################################################
def decode_token(token: str, verify_exp: bool = True) -> dict:
    options = {"verify_exp": verify_exp}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options=options)
        return payload
    except JWTError as exc:
        raise
