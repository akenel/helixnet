"""
Database configuration and session management for SQLAlchemy Async and Sync. 🛠️
This file provides the engine, base, and session factories for interacting with PostgreSQL.
"""
import contextlib
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from contextlib import contextmanager
# 🔑 CRITICAL CHANGE: Import the factory function, NOT the global variable
from app.core.config import get_settings 
from typing import AsyncGenerator
# Set up logging for clarity
logging.basicConfig()
logger = logging.getLogger(__name__)

# Load settings once at a stable time for access within the file
settings = get_settings() # Safe to call here now that it's cached.

# --- 🅰️ Base Class for Declarative Models ---
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models. 🏗️"""
    pass

# ====================================================================
# A. ASYNCHRONOUS DATABASE SETUP (For FastAPI routes) 🚀
# ====================================================================

# 1. Asynchronous Engine
# FIX: Renamed 'engine' to 'async_engine' to match the import name in app/main.py
async_engine = create_async_engine( 
    settings.POSTGRES_ASYNC_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    pool_pre_ping=True,
)
logger.info("Async engine created.")

# 2. Asynchronous Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, # Bind to the renamed engine
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. Asynchronous Session Context Manager
@contextlib.asynccontextmanager
async def get_db_session_context() -> AsyncSession:
    """Provides an asynchronous database session as a context manager."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.error("Database transaction rolled back.")
            raise

# 💡 Function dependency for FastAPI (uses the context manager)
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an asynchronous database session for FastAPI dependencies."""
    async with get_db_session_context() as session:
        yield session
    
# ====================================================================
# B. SYNCHRONOUS DATABASE SETUP (For Celery Workers & Scripts) ⚙️
# ====================================================================

# 1. Synchronous Engine
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
    """Provides a thread-local synchronous session for Celery/Scripts/Tests."""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit() # 💡 Added commit here for task simplicity (Celery tasks will commit)
    except Exception:
        db.rollback()
        logger.error("Synchronous database transaction rolled back.")
        raise
    finally:
        db.close()
