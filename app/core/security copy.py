from asyncio.log import logger
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.services.auth_service import AuthService
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- 🎯 Essential External Imports (PLACEHOLDERS) ---
# NOTE: These are crucial and must point to your actual file locations.

# 1. SQLAlchemy Model: Used to fetch the user record from the database.
from app.db.models.user_model import User 
# 2. Database Dependency: The function that yields an AsyncSession.
# We are using get_db_session to match the common project structure and your traceback.
from app.db.database import get_db_session 
# ----------------------------------------------------------------------


# ======================================================================
# ⚙️ CONFIGURATION & INITIALIZATION
# ======================================================================

# JWT Settings
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_HERE" # ⚠️ CRITICAL: CHANGE THIS IN PRODUCTION ENVIRONMENT!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Set token lifetime (e.g., 60 minutes)

# Password Hashing Context (Bcrypt is the preferred, secure default)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme: Defines where FastAPI looks for the token (Bearer header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


# ======================================================================
# 🔑 PASSWORD HASHING UTILITIES
# ======================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks a plain text password against a bcrypt hash.
    
    :param plain_password: The raw password input by the user.
    :param hashed_password: The stored hashed password from the database.
    :return: True if the passwords match, False otherwise.
    """
    # 🥋 Chuck Norris QA Check: Does the plain text match the secret code?
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates a secure bcrypt hash for a given password.
    
    :param password: The raw password to hash.
    :return: The generated hash string.
    """
    return pwd_context.hash(password)


# ======================================================================
# 🛡️ JWT TOKEN UTILITIES
# ======================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JSON Web Token (JWT) for authentication.
    
    :param data: Dictionary containing the payload (e.g., {"user_id": user_id}).
    :param expires_delta: Optional timedelta for custom expiration; uses default if None.
    :return: The encoded JWT string.
    """
    to_encode = data.copy()
    
    # 1. Set Expiration Time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 2. Add expiration (exp) and subject (sub) claims
    access_token_data = {"user_id": str(User.id)}
    # Sub is usually set to a unique identifier for the user.
    to_encode.update({"exp": expire, "sub": access_token_data})
    
    # 3. Encode the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ======================================================================
# ⚔️ FASTAPI DEPENDENCIES
# ======================================================================

# Custom exception for failed credentials
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials or user is inactive",
    headers={"WWW-Authenticate": "Bearer"},
)

async def get_current_user(
    db: AsyncSession = Depends(get_db_session), 
    token: str = Depends(oauth2_scheme)
) -> User: 
    """
    Dependency to decode the JWT, find the user ID, and fetch the User model 
    instance from the database. This does NOT check if the user is active/banned.
    
    :return: The SQLAlchemy User model instance.
    :raises HTTPException 401: If token is invalid or user not found.
    """
    user_id = None
    
    # 1. Decode the Token and Extract Payload
    try:
        # 🥋 Chuck Norris QA Check: Is the token authentic?
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        
        if user_id_str is None:
            raise CREDENTIALS_EXCEPTION
        
        # 2. Convert to UUID (or appropriate ID type)
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise CREDENTIALS_EXCEPTION

    except JWTError:
        # Handle all JWT-related errors (expiration, bad signature, etc.)
        raise CREDENTIALS_EXCEPTION
    
    # 3. Fetch User from Database (FIX for TypeError: AsyncSession cannot be called)
    # 🛠️ FIX: We use the session object 'db' with the .get() method.
    user: Optional[User] = await db.get(User, user_id)

    if user is None:
        # 🥋 Chuck Norris QA Check: Did the user exist in the DB?
        raise CREDENTIALS_EXCEPTION
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures the authenticated user is also active.
    
    :param current_user: The User model instance returned by get_current_user.
    :raises HTTPException 400: If the user is inactive.
    :return: The active User model instance.
    """
    # 🥋 Chuck Norris QA Check: Is the user active (not banned/disabled)?
    if not current_user.is_active:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST, 
             detail="Inactive user"
         )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency that verifies the currently authenticated, active user 
    is a Superuser (Admin).
    
    :param current_user: The active User model instance.
    :raises HTTPException 403: If the user lacks admin privileges.
    :return: The User model instance, confirmed to be an admin.
    """
    # 🥋 Chuck Norris QA Check: Does the user have admin access? (The final chop!)
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges."
        )
    return current_user
# -----------------------------------------------------------------------------
# 🔗 Dependency Injector for AuthService
# -----------------------------------------------------------------------------
def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    DI helper: Creates and returns an AuthService instance linked to the current DB session.
    """
    logger.debug("[DI] Injecting AuthService with current DB session.")
    return AuthService(db)