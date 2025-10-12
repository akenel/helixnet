# app/services/user_service.py
"""
Service layer functions for user management (creation, retrieval, hashing, auth).
app/services/user_service.py
This handles all business logic interaction with the User model and external services (JWT/Bcrypt).
"""
import uuid
import logging
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, UTC 

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import SecurityScopes 

# 💾 DATABASE AND CORE IMPORTS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.database import get_db_session 
from app.db.models.user_model import User # Assuming User model is correct

# 🔑 CRITICAL AUTH IMPORTS
from jose import ExpiredSignatureError, JWTError, jwt
from app.core.config import settings
from app.core.security import (
    oauth2_scheme,
    verify_password,
    get_password_hash,
    SECRET_KEY, # Required for JWT decode/encode in this file
    ALGORITHM,  # Required for JWT decode/encode in this file
)
# -----------------------------------------------------------------------------
# --- 🛠️ Configuration and Setup ---
# -----------------------------------------------------------------------------
# Logger: use the app logger — already configured elsewhere (recommended).
# For "double docker logging" we will BOTH log via logger and print() to stdout.
# -----------------------------------------------------------------------------
logger = logging.getLogger("helix.auth")  # give it a specific channel for clarity
logger.setLevel(logging.INFO)
# -----------------------------------------------------------------------------
# Helpful small helper for consistent dual logging
# -----------------------------------------------------------------------------
def _log(level: str, message: str, **extra):
    """
    Dual-log helper: sends to logger and prints to stdout so 'docker logs -f'
    shows both (instant info + structured logs).
    """
    # logger call
    if level == "debug":
        logger.debug(message, extra=extra)
    elif level == "info":
        logger.info(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    elif level == "error":
        logger.error(message, extra=extra)
    else:
        logger.info(message, extra=extra)

    # immediate stdout (helps when tailing container logs)
    print(f"[helix.auth][{level.upper()}] {datetime.now(timezone.utc).isoformat()} - {message}", flush=True)
# ======================================================================
# 🌱 INITIALIZATION & SEEDING (Business Logic)
# ======================================================================

async def create_initial_users(db: AsyncSession) -> None:
    """
    🚀 Creates initial users in the database if they don't exist (for development).
    """
    _log("info", "🌱 Starting initial user seeding process...")
    
    # Expanded list for robust testing and seeding
    initial_users = [
        {"email": "admin@helix.net", "password": "admin", "is_active": True, "is_admin": True},
        {"email": "demo@helix.net", "password": "demo", "is_active": True},
        {"email": "test@helix.net", "password": "test", "is_active": True},
        {"email": "chuck@helix.net", "password": "chuck", "is_active": True, "is_admin": True},
        {"email": "marcel@helix.net", "password": "marcel", "is_active": True},
        {"email": "petar@helix.net", "password": "petar", "is_active": True},
        {"email": "cn@helix.net", "password": "CN", "is_active": True, "is_admin": True},
 ] 
    try:
        for user_data in initial_users:
            email = user_data["email"]
            is_admin = user_data.get("is_admin", False)
            
            # 💥 KICK 1 & 2: Derive the non-nullable username
            # This must happen before checking for existence and before User instantiation.
            username = email.split('@')[0]
            
            # Check if user exists asynchronously (by email)
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                # Use imported get_password_hash
                hashed_password = get_password_hash(user_data["password"]) 
        
                db_user = User(
                    id=uuid.uuid4(),
                    email=email,
                    username=username, # ✅ Correctly inserting non-nullable username
                    hashed_password=hashed_password,
                    is_active=user_data.get("is_active", True),
                    is_admin=is_admin,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    # Removed redundant/incorrect parameters that were causing issues:
                    # hashed_password=hashed_password, 
                    # is_admin=is_admin, 
                )
                db.add(db_user)

                # 💥 KICK 3: Clean, accurate logging
                _log("info", f"✨ Created new account: {email} | Username: {username} | Admin: {is_admin}")
            else:
                # Clean logging for existing users
                _log("info", f"👉 Account already exists: {email} | Username (assumed): {username}")

        await db.commit()
        _log("info", "✅ Initial user seeding completed successfully!")

    except Exception as e:
        _log("error", f"❌ CRITICAL Error during user seeding: {e}")
        _log("error", f"❌ Full traceback:\n{traceback.format_exc()}")
        await db.rollback()
        raise

# ======================================================================
# 💾 DATABASE CRUD OPERATIONS
# ======================================================================

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """
    🔍 Get a user by their ID.
    """
    logger.info(f"🔍 [USER_SVC] Retrieving user by ID: {user_id}")
    stmt = select(User).where(User.id == user_id) 
    result = await db.scalars(stmt)
    user = result.first()
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    📧 Asynchronously retrieves a user from the database by their email address.
    """
    logger.info(f"🔍 [USER_SVC] Attempting to retrieve user by email: '{email}'.")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    return user

async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[User]:
    """
    📚 Get a list of users with pagination.
    """
    logger.info(f"📚 [USER_SVC] Fetching users (skip: {skip}, limit: {limit}).")
    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.scalars(stmt)
    return list(result.all())

async def create_user(db: AsyncSession, user_in: Any) -> User:
    """
    ✨ Create a new user, checking for existence and hashing the password.
    """
    logger.info(f"✨ [USER_SVC] Starting creation of new user: '{user_in.email}'.")

    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )
        
    # User creation requires a username; default derivation if not provided
    if not hasattr(user_in, 'username') or not user_in.username:
        # Default to email prefix
        username_to_use = user_in.email.split('@')[0]
    else:
        username_to_use = user_in.username

    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        email=user_in.email,
        username=username_to_use, # Injecting username
        hashed_password=hashed_password,
        is_active=getattr(user_in, 'is_active', True), 
        is_admin=getattr(user_in, 'is_admin', False),
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"🥳 [USER_SVC] User creation complete! New User ID: {db_user.id}.")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user creation for {user_in.email}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user creation.",
        )

async def update_user(
    db: AsyncSession, user_id: uuid.UUID, user_update: Any
) -> Optional[User]:
    """
    ✏️ Update a user's information.
    """
    logger.info(f"✏️ [USER_SVC] Starting update for User ID: {user_id}.")
    try:
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await db.scalars(stmt)
        db_user = result.first()

        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True) 

        if "password" in update_data and update_data["password"] is not None:
            logger.info("🔑 [USER_SVC] Password field detected; hashing new password.")
            setattr(
                db_user,
                "hashed_password",
                get_password_hash(update_data.pop("password")),
            )

        for key, value in update_data.items():
            if value is not None:
                setattr(db_user, key, value)
        
        # Manually update timestamp (if not using ORM hook)
        db_user.updated_at = datetime.now(UTC) 

        await db.commit()
        await db.refresh(db_user)
        logger.info(f"💾 [USER_SVC] User ID {user_id} updated successfully.")
        return db_user

    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user update for {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user update.",
        )

async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """
    🗑️ Delete a user by their ID.
    """
    logger.warning(f"🗑️ [USER_SVC] Attempting to DELETE User ID: {user_id}.")
    try:
        stmt = delete(User).where(User.id == user_id) 
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(
            f"💥 [USER_SVC] Database error during user deletion for {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user deletion.",
        )

# ======================================================================
# 👤 Authentication FOR CURRENT USER
# ======================================================================
async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[Dict[str, Any]]:
    """
    🔓 Looks up user by email and verifies the password hash for login.
    Returns payload data required for JWT creation on success.
    """
    logger.info(f"🔓 [AUTH_SVC] Starting authentication attempt for email: '{email}'.")

    user = await get_user_by_email(db, email)

    if not user:
        logger.warning("🚫 [AUTH_SVC] Authentication failed: User not found.")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning("❌ [AUTH_SVC] Authentication failed: Incorrect password.")
        return None

    if not user.is_active:
        logger.warning(f"🛑 [AUTH_SVC] Authentication denied: User '{email}' is inactive.")
        return None

    # Success! Return the essential data required for JWT creation.
    return {
        "sub": str(user.id), 
        "email": user.email,
        "is_active": user.is_active,
        "scopes": ["read"] + (["admin"] if user.is_admin else [])
    }

# ======================================================================
# 🔑 get_current_user Dependency — Robust and Cleaned and CN-OH approved
# oauth2_scheme should be declared globally in your security module
# ======================================================================
async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(  
        __import__("app.core.security", fromlist=["oauth2_scheme"]).oauth2_scheme  ),
) -> User:
    """
    🔑 Dependency: validate JWT access token, fetch user from DB, and enforce scopes.
    - Requires an *access* token (tokens have "type":"access" in payload).
    - Verifies expiry and signature.
    - Ensures the user exists and is active.
    - Enforces scopes requested by the endpoint via SecurityScopes.

    Returns:
        User (ORM instance) — ready to use by endpoint logic.
    Raises:
        HTTPException(401) when credentials invalid / expired.
        HTTPException(403) when scopes insufficient.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
    )

    # ---------- Quick guard: token must be present ----------
    if not token:
        _log("warning", "No token provided in request (Authorization header missing).")
        raise credentials_exception

    # ---------- Step 1: Decode & validate token ----------
    try:
        # jose.jwt.decode validates signature and exp by default — ExpiredSignatureError raised if expired
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        _log("debug", "Token decoded successfully.", token_sub=payload.get("sub"))
    except ExpiredSignatureError:
        # Access token has expired — explicit message for diagnostics
        _log("error", "💥 [AUTH_DEP] Access token expired.")
        raise credentials_exception
    except JWTError as exc:
        # Any other JWT problem: invalid signature, malformed token, etc.
        _log("error", f"💥 [AUTH_DEP] JWT Error: {exc}")
        raise credentials_exception

    # ---------- Step 2: Enforce token 'type' is access ----------
    token_type = payload.get("type")
    if token_type != "access":
        _log("warning", "Token type is not 'access' — possible refresh token used by mistake.", token_type=token_type)
        raise credentials_exception

    # ---------- Step 3: Extract subject (user id) and token scopes ----------
    user_id_str = payload.get("sub")
    token_scopes: List[str] = payload.get("scopes", [])

    if user_id_str is None:
        _log("error", "Token missing 'sub' claim (user id).")
        raise credentials_exception

    # ---------- Step 4: Convert sub -> UUID ----------
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        _log("error", "User ID in token is not a valid UUID.", raw_sub=user_id_str)
        raise credentials_exception

    # ---------- Step 5: Fetch user from DB ----------
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.scalars(stmt)
        user = result.first()
    except Exception as exc:
        # Any DB problem should be clearly logged — helpful when tailing container logs
        _log("error", "Database error while fetching user.", error=str(exc), user_id=str(user_id))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if user is None:
        _log("warning", f"🚫 [AUTH_DEP] User ID {user_id} found in token, but not in DB.")
        raise credentials_exception

    # ---------- Step 6: Is the user active? ----------
    if not getattr(user, "is_active", True):
        _log("warning", f"🚫 [AUTH_DEP] User ID {user_id} is inactive.", user_email=getattr(user, "email", None))
        raise credentials_exception

    # ---------- Step 7: Scope checks (ensure every required scope is present) ----------
    missing_scopes = [scope for scope in security_scopes.scopes if scope not in token_scopes]
    if missing_scopes:
        _log(
            "warning",
            f"🚫 [AUTH_DEP] User {getattr(user, 'email', user_id)} missing required scopes: {missing_scopes}",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions: Missing required scopes: {missing_scopes}",
        )

    # ---------- All good: return user ----------
    _log("info", "✅ [AUTH_DEP] User authenticated successfully.", user_email=getattr(user, "email", None))
    return user
