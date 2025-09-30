import os
# Import Base/DeclarativeBase for ORM definitions
from sqlalchemy.orm import DeclarativeBase 
# Async imports
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- 1. Base Class Definition (Source of Truth) ---
class Base(DeclarativeBase):
    """
    Base class which provides automated table name 
    and other common features for all models.
    """
    pass

# --- 2. Environment Configuration ---
# Constructs the async database URL from environment variables, 
# defaulting to Docker Compose settings for local development.
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.environ.get('POSTGRES_USER', 'helix_user')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'helix_pass')}@"
    f"{os.environ.get('POSTGRES_HOST', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'helix_db')}"
)

# 3. Create the asynchronous engine
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,  # Set to True to see SQL queries for debugging
    pool_size=20, # Recommended pool size for an async web app
    max_overflow=0
)

# 4. Define the asynchronous session maker
# NOTE: Renamed to SessionLocal to FIX the Import Error in db_utils.py.
# This object is an AsyncSession factory.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 5. Dependency for getting an asynchronous session (for FastAPI endpoints)
async def get_db_session():
    """
    Dependency that yields an AsyncSession for use in FastAPI route handlers.
    It automatically handles closing the session after the request is complete.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
