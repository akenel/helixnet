# ==========================================
# 💾 DB Initialization & User Seeding Script
# ==========================================
# Purpose: Ensures database tables exist and seeds default user accounts.

import asyncio
import logging
from typing import Dict, Any, List
from uuid import uuid4
from contextlib import (
    asynccontextmanager,
)  # 🔑 Import contextlib for safe session handling

# --- Core Imports ---
# We assume Base, async_engine, and get_db_session are defined in app.db.database.
from app.db.database import Base, async_engine, get_db_session
from app.db.models.user import User
from app.db.models.job_result import JobResult  # Included for completeness
from app.services.user_service import (
    get_password_hash,
    get_user_by_email,
)

# --- Setup Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Seed Data ---
SEED_USERS: List[Dict[str, Any]] = [
    {"email": "marcel@helix.net", "password": "marcel", "is_active": True},
    {"email": "petar@helix.net", "password": "petar", "is_active": True},
    {"email": "auditor@helix.net", "password": "auditor", "is_active": True},
    {"email": "chuck@example.com", "password": "chuck", "is_active": True},
]


# 🔑 FIX: Create a context manager helper to safely manage the async generator session.
@asynccontextmanager
async def get_script_session():
    """
    Safely yields the session from the generator and handles closure.
    This replaces the problematic manual anext/aclose sequence.
    """
    # Get the generator object
    db_generator = get_db_session()
    try:
        # Start the generator and retrieve the session.
        # We use __anext__() for maximum compatibility.
        db = await db_generator.__anext__()
        yield db
    except Exception as e:
        logger.error(f"🚨 Unhandled error in session context: {e}")
        raise  # Re-raise after logging
    finally:
        # Ensure the generator is stopped/closed correctly.
        await db_generator.aclose()


async def init_db():
    """Initializes the database by creating all defined tables."""
    logger.info("⏳ Running Base.metadata.create_all...")
    async with async_engine.begin() as conn:
        # Note: This checks if tables exist before creating them.
        await conn.run_sync(Base.metadata.create_all)
    logger.info("🚀 Database tables initialized successfully.")


# --- Helper Function (Cleaned up from original) ---
async def create_user_with_hashed_password(
    db, email: str, hashed_password: str, is_active: bool
) -> User:
    """Creates user using the pre-hashed password directly and commits."""
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
    )
    db.add(new_user)
    # The commit here makes the transaction permanent for this user.
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def seed_users():
    """Seeds default users into the database if they don't already exist."""
    logger.info("Database seeding started... 🌱")

    # 1. Initialize DB (ensures tables exist)
    await init_db()

    # 2. Use the safe context manager to acquire and release the database session
    async with get_script_session() as db:
        try:
            for user_data in SEED_USERS:
                email = user_data["email"]
                password = user_data["password"]

                # Check if user already exists
                existing_user = await get_user_by_email(db, email)

                if existing_user:
                    logger.warning(f"⚠️ User '{email}' already exists. Skipping.")
                    continue

                # Hash the password
                hashed_password = get_password_hash(password)

                # Create the user and commit
                new_user = await create_user_with_hashed_password(
                    db,
                    email=email,
                    hashed_password=hashed_password,
                    is_active=user_data["is_active"],
                )

                logger.info(
                    f"🥳 User '{email}' created successfully! ID: {new_user.id}"
                )

        except Exception as e:
            # If any failure occurs during the loop, this is handled by the outer try/except.
            logger.error(f"🚨 Error during seeding: {e}")
            raise  # Re-raise to signal a failure to the 'make' process

    # The context manager ensures a clean exit here without an implicit rollback log.
    logger.info("Database seeding successfully completed. 🏁")


if __name__ == "__main__":
    try:
        # Use a higher logging level for SQLAlchemy to keep the output cleaner
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        asyncio.run(seed_users())
    except Exception as e:
        logger.error(f"Fatal error during script execution: {e}")
