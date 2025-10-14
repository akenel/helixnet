# /app/core/security.py
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List, Dict

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger("app/core/security")

# ============================================================
# PASSWORD HASHING
# ============================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# TOKEN CONFIG
# ============================================================
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    scopes={
        "admin": "Administrator access",
        "user": "Regular user access",
        "test": "Testing role",
        "audit": "Audit read-only",
        "guest": "Guest read-only",
    },
)


# ============================================================
# TOKEN CREATION
# ============================================================
def create_access_token(
    *,
    subject: Union[str, uuid.UUID],
    scopes: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = _now()
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(subject),
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    *,
    subject: Union[str, uuid.UUID],
    scopes: List[str],
    expires_delta: Optional[timedelta] = None,
) -> Dict[str, str]:
    """
    Creates and returns a refresh token + metadata for persistence.
    """
    now = _now()
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(subject),
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": jti,
    }

    encoded = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": encoded, "jti": jti, "expires_at": expire.isoformat()}


# ============================================================
# TOKEN DECODING / VALIDATION
# ============================================================
def decode_token(token: str, verify_exp: bool = True) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": verify_exp},
        )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing subject in token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate UUID-ish subject
        try:
            uuid.UUID(str(sub))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid subject UUID in token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
