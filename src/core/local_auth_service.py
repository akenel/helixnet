# src/core/security.py
import logging
import uuid
from typing import Annotated, Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user_model import UserModel
from src.db.database import get_db_session
from src.core.config import settings

logger = logging.getLogger("src/core/local_auth_service.py")
logger.setLevel(logging.INFO)

# ==========================================================
# CONFIG
# ==========================================================
ALGORITHM = settings.KEYCLOAK_ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials or user is inactive",
    headers={"WWW-Authenticate": "Bearer"},
)

# ======================================================================
# 🛡️ JWT TOKEN UTILITIES
# ======================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ======================================================================
# 🧩 TOKEN DECODING
# ======================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
        return payload
    except JWTError:
        logger.error("JWT decoding failed.")
        raise CREDENTIALS_EXCEPTION


async def get_current_user_local(
    db: AsyncSession = Depends(get_db_session), token: str = Depends(oauth2_scheme)
) -> UserModel:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise CREDENTIALS_EXCEPTION

        user = await db.get(UserModel, uuid.UUID(user_id))
        if user is None:
            raise CREDENTIALS_EXCEPTION
        return user
    except JWTError:
        raise CREDENTIALS_EXCEPTION


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user_local),
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges.",
        )
    return current_user

ActiveUserPayload = Annotated[Dict[str, Any], Depends(get_current_user)]
