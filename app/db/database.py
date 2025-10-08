# cd ~/repos/helixnet/app/test
# TESTING=True POSTGRES_HOST=127.0.0.1 CELERY_BROKER_URL="redis://127.0.0.1:6379/0" CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/0" pytest test_job_flow.py
import os
import contextlib
import logging
from typing import AsyncGenerator
from contextlib import contextmanager
# **Crucially, you must also set the `TESTING=True` environment variable when running your tests:**
# (.venv) angel@debian:~/repos/helixnet/app/tests$ TESTING=True POSTGRES_HOST=127.0.0.1 pytest test_job_flow.py

from sqlalchemy import create_engine
# 💡 NEW: Import NullPool for test environment fix
from sqlalchemy.pool import NullPool 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# 🔑 CRITICAL: Import configuration utility
# Assuming this factory function provides your settings object
from app.core.config import get_settings 
# In app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# Add this import:
from sqlalchemy.pool import NullPool # Import to disable pooling

# ====================================================================
# 📝 Configuration & Logging ⚙️
# ====================================================================
import os
import contextlib
import logging
from typing import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine
# 💡 NEW: Import NullPool for test environment fix
from sqlalchemy.pool import NullPool 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

# 🔑 CRITICAL: Import configuration utility
# Assuming this factory function provides your settings object
from app.core.config import get_settings 

# ====================================================================
# 📝 Configuration & Logging ⚙️
# ====================================================================

# Set up logging for clarity
logging.basicConfig()
logger = logging.getLogger(__name__)

# Load settings object (safe since it's cached/singleton)
settings = get_settings() 

# Environment check: Determine if we are running in a test environment (for fixes)
# FIX: Checking for the 'TESTING' variable used in the shell command
IS_TESTING = os.getenv("TESTING", "False").lower() in ('true', '1', 't')
if IS_TESTING:
    logger.warning("Environment detected as TEST. Applying NullPool and pool_pre_ping=False fixes.")


# ====================================================================
# 🧱 Base Class for Models 🏗️
# ====================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models. Models inherit from this."""
    pass


# ====================================================================
# A. ASYNCHRONOUS DATABASE SETUP (For FastAPI Routes) 🚀
# ====================================================================

# Build engine arguments, applying the test fix when necessary
async_engine_kwargs = {
    "echo": settings.DB_ECHO,
    # 💥 CRITICAL FIX 1: Disable connection pooling in tests (set to NullPool)
    "poolclass": NullPool if IS_TESTING else None,
    # 💥 CRITICAL FIX 2: Disable pre-ping in tests (still necessary even with NullPool)
    "pool_pre_ping": False if IS_TESTING else True,
}

# FIX: Only include pool_size if we are NOT in testing mode, as NullPool does not accept this argument.
if not IS_TESTING:
    async_engine_kwargs["pool_size"] = settings.DB_POOL_SIZE


# 1. Asynchronous Engine
async_engine = create_async_engine( 
    settings.POSTGRES_ASYNC_URL,
    **async_engine_kwargs,
    future=True # SQLAlchemy 2.0 style
)
logger.info(f"Async engine created. Pool class: {'NullPool' if IS_TESTING else 'Default'}")


# 🔑 LEGACY/COMPATIBILITY FIX: 'database' variable
# The main application (app/main.py) expects to import 'database'. 
# This was likely an instance of the 'databases' library. Since we've transitioned
# to SQLAlchemy async, we define 'database' as the raw engine object for compatibility
# to prevent the ImportError. The actual usage of 'database' in app.main should be checked.
database = async_engine 
# ----------------------------------------------------


# 2. Asynchronous Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True # SQLAlchemy 2.0 style
)


# 3. Asynchronous Session Context Manager
@contextlib.asynccontextmanager
async def get_db_session_context() -> AsyncSession:
    """Provides an asynchronous database session as a context manager for manual use."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            # Log the rollback for debugging
            logger.error("Async database transaction rolled back.")
            raise

# 4. Asynchronous Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session for FastAPI dependencies."""
    async with get_db_session_context() as session:
        yield session
    
# 5. Engine Shutdown Helper 🛑
async def close_async_engine():
    """Explicitly closes the SQLAlchemy async engine connections."""
    logger.info("Closing SQLAlchemy Async Engine connections...")
    await async_engine.dispose()
    logger.info("SQLAlchemy Async Engine disposed.")


# ====================================================================
# B. SYNCHRONOUS DATABASE SETUP (For Scripts/Workers) ⚙️
# ====================================================================

# 1. Synchronous Engine
# Synch engines do not suffer the same event loop issues as the async ones in testing.
SyncEngine = create_engine(
    settings.POSTGRES_SYNC_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    pool_pre_ping=True,
)
logger.info("Sync engine created.")


# 2. Synchronous Session Factory
SyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=SyncEngine,
    class_=Session
)

# 3. Synchronous Session Context Manager
@contextmanager
def get_db_session_sync() -> Session:
    """Provides a thread-local synchronous session for Celery/Scripts/Tests (via sync engine)."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Synchronous database transaction rolled rolled back.")
        raise
    finally:
        db.close()
