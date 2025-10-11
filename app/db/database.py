# 1. 📂 app/db/database.py (The Database Core)
import os
import logging
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncGenerator

# 📚 Core SQLAlchemy/Connection Imports
from requests import session  # ⚠️ NOTE: This import is probably wrong; SQLAlchemy uses its own Session/sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ⚙️ Configuration
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("db_setup")
logger.setLevel(logging.INFO)

# 📝 Environment Check
IS_TESTING = os.getenv("TESTING", "False").lower() in ("true", "1", "t")
logger.info(f"✨ Script loaded. TESTING mode: {IS_TESTING}")


# ====================================================================
# 🧱 Base Class and Model Registration 🏗️
# ====================================================================
logger.info("📐 Step 1: Defining SQLAlchemy Base Class.")
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass
logger.info("✅ Base Class Defined.")


# 💥 CRITICAL FIX: Explicitly import all model files to register them to Base.metadata
logger.info("🔗 Step 2: Forcing Model Imports to Register Tables...")
try:
    # These imports force the model files to execute, registering the table metadata.
    import app.db.models.user_model
    logger.info("   -> Imported user_model. Table 'users' should be registered.")
    import app.db.models.job_model
    logger.info("   -> Imported job_model. Table 'jobs' should be registered.")
    import app.db.models.artifact_model
    logger.info("   -> Imported artifact_model. Table 'artifacts' should be registered.")
    # Add any other missing models here:
    # import app.db.models.team_model
    # import app.db.models.task_model
    
except ImportError as e:
    logger.error(f"❌ FATAL IMPORT ERROR: Model path is wrong or missing: {e}")
    # This will give a clear traceback if the file path (e.g., app.db.models.user_model) is incorrect.
    raise
    
registered_tables = list(Base.metadata.tables.keys())
logger.info(f"✅ Model Registration Complete. Found Tables: {registered_tables} 🥳")
if 'users' not in registered_tables:
    logger.error("🚨 CRITICAL: The 'users' table is still missing after imports! Check user_model.py imports.")
    
    
# ====================================================================
# A. ASYNCHRONOUS DATABASE SETUP (FastAPI) 🚀
# ====================================================================

# 1. Asynchronous Engine Configuration
async_engine_kwargs = {
    "echo": settings.DB_ECHO,
    "future": True,
}
logger.info("🛠️ Configuring Async Engine...")

if IS_TESTING:
    async_engine_kwargs["poolclass"] = NullPool
    async_engine_kwargs["pool_pre_ping"] = False
    logger.warning("   -> TEST CONFIG: Using NullPool.")
else:
    async_engine_kwargs["pool_pre_ping"] = True
    async_engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    logger.info(f"   -> PROD CONFIG: Pool Size {settings.DB_POOL_SIZE}.")


# 2. Asynchronous Engine Creation
async_engine = create_async_engine(
    settings.POSTGRES_ASYNC_URL,
    **async_engine_kwargs,
)
logger.info(f"✅ Async Engine Created.")


# 3. Asynchronous Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)
logger.info("✅ Async Session Factory (AsyncSessionLocal) Ready.")


# 4. Asynchronous Dependencies for FastAPI
@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Provides an async database session context manager."""
    logger.info("➡️ Entering get_db_session_context.")
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
        logger.info("⬆️ Async transaction committed.")
    except Exception:
        await session.rollback()
        logger.error("❌ Async transaction rolled back.", exc_info=True)
        raise
    finally:
        await session.close()
        logger.info("⬅️ Async session closed.")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session."""
    logger.info("➡️ FastAPI Dependency: Yielding Async Session.")
    async with get_db_session_context() as session:
        yield session


# 5. Initialization and Shutdown Helpers
async def init_db_tables():
    """Create all tables defined by Base.metadata if they do not exist."""
    
    current_tables = list(Base.metadata.tables.keys())
    logger.info(f"📦 Step 3: Running init_db_tables. Tables found: {current_tables}") 

    async with async_engine.begin() as conn:
        logger.info("🔄 Beginning database connection for creation...")
        # CRITICAL STEP: Run the synchronous DDL command inside the async connection
        await conn.run_sync(Base.metadata.create_all) 
        logger.info("✅ Database table initialization complete (Base.metadata.create_all called).")

async def close_async_engine():
    """Explicitly closes the SQLAlchemy async engine connections."""
    logger.info("🛑 Step 4: Closing SQLAlchemy Async Engine connections...")
    await async_engine.dispose()
    logger.info("✅ SQLAlchemy Async Engine disposed.")


# ====================================================================
# B. SYNCHRONOUS DATABASE SETUP (Celery/Scripts) ⚙️
# ====================================================================

# 1. Synchronous Engine Creation
logger.info("🛠️ Configuring Sync Engine...")
SyncEngine = create_engine(
    settings.POSTGRES_SYNC_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    pool_pre_ping=True,
    future=True,
)
logger.info("✅ Sync Engine Created.")

# 2. Synchronous Session Factory
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=SyncEngine,
    class_=Session,
    future=True,
)
logger.info("✅ Sync Session Factory (SyncSessionLocal) Ready.")

# 3. Synchronous Session Context Manager
@contextmanager
def get_db_session_sync() -> session:
    """Provides a thread-local synchronous session."""
    logger.info("➡️ Entering get_db_session_sync.")
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
        logger.info("⬆️ Sync transaction committed.")
    except Exception:
        db.rollback()
        logger.error("❌ Synchronous transaction rolled back.", exc_info=True)
        raise
    finally:
        db.close()
        logger.info("⬅️ Sync session closed.")