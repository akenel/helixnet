# app/db/database.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session as session, DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    AsyncEngine,
)
# ================================================================
from app.core.config import settings, get_settings
from app.db.models.base import Base # Assuming Base is imported here
# ================================================================
logger = logging.getLogger("helix🛠️db")
logger.setLevel(logging.INFO)
settings = get_settings()
# ================================================================
# --- Engine Definitions ---
SyncSessionLocal: Optional[sessionmaker] = None
# ================================================================
# ⚙️ ASYNC ENGINE & SESSION DEFINITION
# ================================================================
# 1. Define the Async Engine
async_engine = create_async_engine(
    settings.POSTGRES_ASYNC_URI,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)
# 2. Define the Async Session Maker
# FIX: 'bind=async_engine' is the critical piece that resolves the UnboundExecutionError.
AsyncSessionLocal = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False, # Essential for using ORM objects outside the session
    autoflush=False
)
# ================================================================
# 🔗 DEPENDENCY FUNCTION (For FastAPI Route Injection)
# ================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Standard FastAPI dependency function for yielding a session in routes.
    Note: Routes using this must still manually commit/rollback changes if desired.
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
# ================================================================
def create_async_engine_instance() -> AsyncEngine:
    """Initializes and returns the AsyncEngine instance."""
    global async_engine
    if async_engine is None:
        logger.info("Initializing async database engine...")
        async_engine = create_async_engine(
            settings.POSTGRES_ASYNC_URI, # Use the computed URL property
            echo=settings.DB_ECHO,        # Use DB_ECHO for consistency
            pool_pre_ping=True, # Ensure connection is alive
            pool_recycle=3600 # Recycle connections after one hour
        )
    return async_engine
# ================================================================

async def close_async_engine() -> None:
    """Closes the async engine and connection pool."""
    global async_engine
    if async_engine:
        logger.info("Closing async database engine...")
        await async_engine.dispose()
        async_engine = None
# ================================================================

async def init_db_tables() -> None:
    """
    Ensures all models are imported (via app.db.__init__.py) and creates 
    tables in the database if they don't already exist.
    """
    engine = create_async_engine_instance()

    # --- ENHANCED LOGGING START ---
    
    # 1. Get all registered table names from Base.metadata
    registered_tables = sorted(Base.metadata.tables.keys())
    
    # 2. Log them clearly
    if registered_tables:
        logger.info("✅ SUCCESS: Found and registered the following ORM models/tables:")
        for table_name in registered_tables:
            logger.info(f"   - {table_name}")
    else:
        # This should ONLY happen if app/db/__init__.py fails to import models
        logger.warning("🚨 WARNING: Base.metadata found NO registered ORM models/tables.")
    
    # --- ENHANCED LOGGING END ---

    async with engine.begin() as conn:
        logger.info("Checking database for missing tables and attempting creation...")
        # We must import all models (via app.db.__init__.py) BEFORE this call
        # to ensure Base.metadata has collected them all.
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database table initialization complete.")

# ================================================================
# --- Session Generators (FastAPI Dependencies) ---
# ================================================================
# ================================================================
# 💉 DEPENDENCY INJECTION CONTEXT MANAGER (For Startup/Lifespan)
# ================================================================
@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a transactional AsyncSession within a context manager.
    Dependency to provide a transactional database session (AsyncSession).
    Used in lifespan hook for setup/seeding. Automatically handles rollback/commit/close.

    """
    if AsyncSessionLocal is None or async_engine is None:
        # Lazy initialization if not already done (useful for scripting)
        create_async_engine_instance() 
        AsyncSessionLocal.configure(bind=async_engine)
        
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

# ================================================================
# Helper function for synchronous contexts (e.g., Celery Worker)
# ================================================================

def create_sync_engine(url: str = settings.POSTGRES_SYNC_URI) -> Engine: 
    """Initializes and returns the synchronous Engine instance."""
    logger.info("Initializing sync database engine...")
    engine = create_engine(
        url, 
        echo=settings.DB_ECHO, 
        pool_pre_ping=True
    )
    return engine
# ================================================================

def get_db_session_sync() -> AsyncGenerator[session, None]: # FIX: Changed return type to generator
    """Provides a synchronous database session (e.g., for Celery worker tasks)."""
    # Note: Celery tasks must use a dedicated synchronous session factory 
    # to avoid issues with event loops.   
    # Declare global SyncSessionLocal here before any use/read of the variable
    global SyncSessionLocal

    if SyncSessionLocal is None:
        engine = create_sync_engine()
        # Initialize the synchronous session factory once
        SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SyncSessionLocal()
    try:
        # FIX: Should yield the session, not return it directly
        yield db 
    finally:
        db.close()

# ================================================================
# 🔨 DATABASE LIFECYCLE FUNCTIONS
# ================================================================
async def init_db_tables():
    """Create all tables in the database."""
    async with async_engine.begin() as conn:
        logger.info("Running DDL to create/verify tables...")
        # Note: 'Base.metadata.create_all' must be run within 'conn.run_sync'
        await conn.run_sync(Base.metadata.create_all)
        logger.info("DDL operation complete.")

async def close_async_engine():
    """Dispose of the async engine on shutdown."""
    await async_engine.dispose()
    logger.info("Async engine disposed.")

