# /app/core/security.py - The Single Source of Truth for Security
# --------------------------------------------------------------------

# 📦 CORE IMPORTS
from datetime import datetime, timedelta, timezone # 💡 Use timezone.utc for time consistency
from typing import Optional, Dict, Any, Union
import logging

# 💾 DEPENDENCY IMPORTS (Keep only what's needed for this low-level file)
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.context import CryptContext  # 🔑 Hashing library
from jose import jwt, JWTError          # 🔐 JWT handling
from pydantic import BaseModel, Field

# ⚙️ APPLICATION CORE IMPORTS
from app.core.config import settings # 🌍 Get config settings
# from app.db.models import User # ⚠️ NOTE: User model should be imported in service/dependency layer


# --- CONFIGURATION & CONSTANTS ---
logger = logging.getLogger(__name__)

# 🔑 Hashing Context: Defines the scheme for password hashing
# Only define this ONCE.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔒 JWT Configuration: Loaded from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


# 💡 Token Payload Schema (Data decoded from JWT)
class TokenData(BaseModel):
    """Schema for the data extracted from a decoded JWT payload."""
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
        "admin": "Admin privileges: full access to sensitive endpoints.",
        "user": "Standard user privileges: general application access.",
    },
)


# ====================================================================
# 🛡️ PASSWORD UTILITIES (The ONE place for hashing/verification)
# ====================================================================

def get_password_hash(password: str) -> str:
    """
    🔒 Generates a secure hash for a given password using CryptContext.
    """
    return pwd_context.hash(password)


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
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 📝 Data to be encoded in the token payload
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "scopes": scopes,  # Inject scopes directly into the token
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
        payload: dict[str, Any] = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        
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