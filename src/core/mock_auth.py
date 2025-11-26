# File: src/core/mock_auth.py
"""
Mock Authentication - TEMPORARY BYPASS for Keycloak issues.
USE ONLY FOR DEVELOPMENT/TESTING!

This provides fake authentication so we can test POS endpoints
while Keycloak realm configuration is being fixed.

DELETE THIS FILE once Keycloak is working properly!
"""
import logging
from uuid import UUID, uuid4
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.database import get_db_session
from src.db.models import UserModel

logger = logging.getLogger(__name__)

# Hardcoded test user IDs (these will be seeded in DB)
MOCK_USERS = {
    "pam": "00000000-0000-0000-0000-000000000001",
    "ralph": "00000000-0000-0000-0000-000000000002",
    "michael": "00000000-0000-0000-0000-000000000003",
    "felix": "00000000-0000-0000-0000-000000000004",
}

# Default to Pam (cashier) for testing
DEFAULT_MOCK_USER = "pam"


async def get_mock_user(
    username: str = DEFAULT_MOCK_USER,
    db: AsyncSession = Depends(get_db_session)
) -> UserModel:
    """
    Return a mock user from the database.

    WARNING: This bypasses ALL authentication!
    Only use for development/testing.
    """
    user_id = MOCK_USERS.get(username, MOCK_USERS[DEFAULT_MOCK_USER])

    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Mock user '{username}' not found in DB! Falling back to any user.")
        # Fallback: get any user
        result = await db.execute(select(UserModel).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            # Last resort: create a temporary fake user
            logger.error("No users in DB! Creating emergency fake user.")
            user = UserModel(
                id=UUID(user_id),
                keycloak_id=uuid4(),
                username=username,
                email=f"{username}@artemis-luzern.local",
                first_name=username.capitalize(),
                last_name="(Test User)",
                is_active=True,
                is_superuser=False
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

    logger.info(f"🔓 MOCK AUTH: Returning user '{user.username}' (ID: {user.id})")
    return user
