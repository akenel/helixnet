from datetime import timedelta, datetime, timezone
from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.core.security import create_access_token, create_refresh_token, decode_token

from app.db.models.refresh_token_model import RefreshToken
from app.db.models.user_model import User
from app.schemas.user_schema import TokenPairOut # Assuming this Pydantic schema is defined

# Load the singleton settings object once
from app.core.config import get_settings, Settings
settings: Settings = get_settings()

class AuthService:
    """
    Service layer for all core authentication and token management logic,
    including token creation, persistence, validation, and revocation.
    """

    async def create_token_pair_for_user(
        self, 
        db: AsyncSession, 
        user: User, 
        scopes: list[str] = ["user"]
    ) -> dict[str, Any]:
        """
        Creates a new access token and a database-persisted refresh token pair.
        """
        # --- 1. ACCESS TOKEN ---
        access_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), 
            scopes=scopes, 
            expires_delta=access_expires
        )

        # --- 2. REFRESH TOKEN LIFETIME ---
        # Choose refresh lifetime based on user properties (e.g., admin gets PRO life)
        if user.is_admin:
            refresh_days = settings.REFRESH_TOKEN_EXPIRE_DAYS_PRO
        else:
            refresh_days = settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT
            
        refresh_expires = timedelta(days=refresh_days)

        # Create the signed JWT refresh token and get its JTI (ID)
        refresh_token, jti, expires_at = create_refresh_token(
            subject=str(user.id), 
            expires_delta=refresh_expires
        )

        # --- 3. PERSIST REFRESH TOKEN RECORD (for Revocation) ---
        db_token = RefreshToken(
            jti=jti,
            user_id=user.id,
            expires_at=expires_at,
            # is_revoked defaults to False in the model
        )
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)
        
        # --- 4. RETURN TOKEN PAIR ---
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "refresh_jti": jti,
            "refresh_expires_at": expires_at.isoformat(),
            "access_expires_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        }

    async def revoke_refresh_jti(self, db: AsyncSession, jti: str) -> None:
        """
        Revokes a single refresh token record using its JTI.
        """
        stmt = update(RefreshToken).where(
            RefreshToken.jti == jti
        ).values(
            is_revoked=True,
            updated_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)
        await db.commit()

    async def verify_refresh_token(self, db: AsyncSession, refresh_token: str) -> Optional[User]:
        """
        Validates a refresh token by decoding it and checking its status in the database.
        Returns the associated User object if valid, otherwise None.
        """
        # 1. Decode the token to get JTI and User ID (SUB)
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            user_id_str = payload.get("sub")
            if not jti or not user_id_str:
                return None
            user_id = UUID(user_id_str)
        except Exception:
            # Token is invalid, expired, or improperly formatted
            return None

        # 2. Check the DB record for existence, revocation, and non-expiry
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False, # Must not be revoked
                RefreshToken.expires_at > datetime.now(timezone.utc) # Must not be past DB expiry
            )
        )
        result = await db.execute(stmt)
        db_token_record: RefreshToken | None = result.scalar_one_or_none()

        if db_token_record is None:
            return None # Token is invalid, revoked, or expired in the DB

        # 3. Load the user associated with the token
        user = await db.get(User, user_id)
        
        # Crucial security check: Ensure the user exists and is active
        if user is None or not user.is_active:
            if db_token_record:
                # If user is inactive/deleted, instantly revoke the token record
                await self.revoke_refresh_jti(db, jti)
            return None

        # 4. Success: Return the active User object
        return user

# Instantiate the service for use in routers/dependencies
auth_service = AuthService()
