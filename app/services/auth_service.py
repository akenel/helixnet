import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, status, Depends
from jose import JWTError

from app.db.models import UserModel, RefreshTokenModel
from app.core import security
from app.core.config import settings
from app.db.database import get_db_session

logger = logging.getLogger("app/services/auth_service")

ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS_DEFAULT)
# now_utc = datetime.now(timezone.utc)


# ---------------------------------------------------------------------
def utc_now_naive() -> datetime:
    """Return UTC now as a naive datetime (for DB writes)."""
    return datetime.utcnow().replace(tzinfo=None)


# ---------------------------------------------------------------------
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        user = result.scalars().first()

        if not user:
            logger.debug(f"[AUTH] User not found: {email}")
            return None

        if not security.verify_password(password, user.hashed_password):
            logger.debug(f"[AUTH] Invalid password for {email}")
            return None

        return user

    async def create_token_pair_for_user(self, user: UserModel) -> Dict[str, Any]:
        """Creates new access + refresh tokens for a user."""
        scopes = getattr(user, "scopes", ["user"])
        now_utc = datetime.now(timezone.utc)

        # --- ACCESS TOKEN ---
        access_token = security.create_access_token(
            subject=user.id,
            scopes=scopes,
            expires_delta=ACCESS_TOKEN_EXPIRE,
        )

        # --- REFRESH TOKEN ---
        refresh_meta = security.create_refresh_token(
            subject=user.id,
            scopes=scopes,
            expires_delta=REFRESH_TOKEN_EXPIRE,
        )

        # Convert aware -> naive for DB compatibility
        expires_at_aware = datetime.fromisoformat(refresh_meta["expires_at"])
        expires_at_naive = expires_at_aware.replace(tzinfo=None)

        # --- SAVE TO DB ---
        refresh_entry = RefreshTokenModel(
            jti=refresh_meta["jti"],
            user_id=user.id,
            expires_at=expires_at_naive,
            is_revoked=False,
        )

        self.db.add(refresh_entry)
        await self.db.commit()

        logger.info(
            f"[AUTH] Tokens created for {user.email} | JTI={refresh_meta['jti']}"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_meta["token"],
            "token_type": "bearer",
        }

    async def verify_and_refresh_token_pair(self, refresh_token: str) -> Dict[str, Any]:
        """Validates refresh token and rotates it."""
        try:
            payload = security.decode_token(refresh_token, verify_exp=True)

            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type.")

            jti = payload.get("jti")
            user_id = payload.get("sub")
            if not jti or not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload.")

            # Find valid token
            stmt = select(RefreshTokenModel).filter(
                RefreshTokenModel.jti == jti,
                RefreshTokenModel.expires_at > utc_now_naive(),
            )
            result = await self.db.execute(stmt)
            db_token = result.scalars().first()

            if not db_token:
                raise HTTPException(
                    status_code=401, detail="Refresh token invalid or expired."
                )

            # One-time use policy: revoke old JTI
            await self.revoke_refresh_jti(jti)

            # Fetch user
            stmt_user = select(UserModel).where(UserModel.id == user_id)
            result_user = await self.db.execute(stmt_user)
            user = result_user.scalars().first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found for token.")

            return await self.create_token_pair_for_user(user)

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AUTH] Refresh failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error refreshing token.")

    async def revoke_refresh_jti(self, jti: str):
        """Deletes refresh token entry by JTI."""
        try:
            stmt = delete(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
            await self.db.execute(stmt)
            await self.db.commit()
            logger.debug(f"[AUTH] Revoked JTI {jti}")
        except Exception as e:
            logger.error(f"[AUTH] Revoke JTI failed: {e}", exc_info=True)


async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)
