# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Hashing library
from passlib.context import CryptContext
# JWT handling
from jose import jwt, JWTError
# FastAPI security
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
# Import from your modules
from app.db.database import get_db_session
from app.schemas.user import UserInDB # Pydantic schema for return type
# 💡 Assuming your User model is here:
from app.db.models.user import User 
# --- Configuration ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 💡 FIX 1: Import only the settings FACTORY
from app.core.config import get_settings 

# 💡 FIX 2: Instantiate the settings object immediately
settings = get_settings()

# 💡 FIX 3: Assign global constants using the instantiated settings object.
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES 

# 💡 FIX 4: Update tokenUrl to use the full, consistent /api/v1 prefix defined in config
# NOTE: The server is currently registering this path as /api/v1/token, not /api/v1/auth/token.
# We adjust the tokenUrl to match the registered endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

# --- Password Hashing Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a hash for a given password."""
    return pwd_context.hash(password)
# --- JWT Token Functions ---
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  
    # CRITICAL FIX: Use 'id' (from the DB model) as the subject, not 'user_id'
    to_encode.update({"exp": expire, "sub": str(data["id"])})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
# --- Dependency for Protected Routes (The Fix for the 401) ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) 
        user_id_str: str = payload.get("sub") 
        if user_id_str is None:
            raise credentials_exception 
        # Query the database for the user using the UUID string from the token
        query = select(User).where(User.id == user_id_str)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception     
        # 💡 NOTE: UserInDB needs to be constructed from the SQLAlchemy model instance 'user'
        # If your User model has a .to_pydantic() or if UserInDB.model_validate(user) works, this is fine.
        return user 
    except JWTError:
        raise credentials_exception
