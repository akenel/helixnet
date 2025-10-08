# app/core/security.py
# ====================================================================
# 📦 EXTERNAL & CORE IMPORTS
# ====================================================================
# Standard library
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Hashing and JWT
from passlib.context import CryptContext  # 🔑 Hashing library
from jose import jwt, JWTError  # 🔐 JWT handling

# FastAPI Security & Dependencies
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)  # 🛡️ For authentication flows

# Application Core
from app.core.config import settings
from app.db.database import get_db_session
from app.schemas.user import UserInDB
from app.db.models.user import User  # 💡 Assuming your User model is here
from uuid import UUID
# app/core/security.py
from pydantic import BaseModel, Field
from typing import Optional

# ====================================================================
# ⚙️ CONFIGURATION & CONSTANTS
# ====================================================================
# 🔑 Hashing Context: Defines the scheme for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 🔒 JWT Configuration: Loaded from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 🚪 OAuth2 Scheme: Defines the token endpoint and available scopes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/token",
    scopes={
        "admin": "Admin privileges: full access to sensitive endpoints.",
        "user": "Standard user privileges: general application access.",
    },
)


# 💡 Token Payload Schema (What the token contains)
class TokenData(BaseModel):
    """
    Schema for the data extracted from a decoded JWT payload.
    It typically contains the 'subject' (sub), which you are mapping to 'email'.
    """

    email: Optional[str] = Field(
        None,
        description="The subject (sub) of the token, typically the user's email or ID.",
    )
    # You might also include scopes or user ID here if your token contains them
    # scopes: list[str] = []
    # user_id: Optional[int] = None


# ====================================================================
# 🛡️ PASSWORD UTILITIES
# ====================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ====================================================================
def get_password_hash(password: str) -> str:
    """
    Generates a secure hash for a given password.
    """
    return pwd_context.hash(password)


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
        expire = datetime.utcnow() + expires_delta
    else:
        # ⏳ Default expiry time if not provided
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 📝 Data to be encoded in the token payload
    to_encode: Dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "scopes": scopes,  # Inject scopes directly into the token
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ====================================================================
async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
) -> UserInDB:
    """
    Dependency function to validate the JWT token, fetch the user,
    and verify the required security scopes.
    """
    # ❌ Setup for unauthorized response
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 🔓 Decode and validate the token signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 👤 Extract subject (user ID) and scopes from the payload
        user_id: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])

        if user_id is None:
            raise credentials_exception

    except JWTError:
        # 💥 Handle errors like invalid signature or expired token
        raise credentials_exception
    # 💾 Fetch user from the database.
    # In get_current_user function:
    stmt = select(User).where(User.id == user_id) 
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # 🧐 Scope Check: Ensure the user's token has *all* required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: Missing required scope '{scope}'",
            )

    # ✅ Return the user object (converted to the safe Pydantic schema)
    return UserInDB.model_validate(user)


# ====================================================================
