# =========================================================================
# ⚙️ TASK DB UTILITIES
# Provides a separate, safe database engine and session dedicated for use
# by Celery worker tasks to avoid FastAPI's dependency injection complexity.
# =========================================================================
import logging
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import database_exists, create_database

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Worker Engine and Session ---

def get_worker_engine():
    """Initializes and returns the database engine for worker use."""
    try:
        # Celery workers are synchronous, so we MUST use the synchronous URL.
        SQLALCHEMY_DATABASE_URL = settings.POSTGRES_SYNC_URL
        
        # We use a separate engine for the worker to manage connections independently
        # from the main FastAPI thread pool.
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            # Adjust connection pool size appropriate for worker load
            pool_size=5,
            max_overflow=10,
        )

        if not database_exists(engine.url):
            logger.info(f"Database does not exist at {SQLALCHEMY_DATABASE_URL}. Creating...")
            create_database(engine.url)

        return engine

    except AttributeError as e:
        # This catches if POSTGRES_SYNC_URL isn't set
        logger.error(f"Failed to create worker database engine: {e}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred during worker database engine creation: {e}")
        raise e

# Create a local session factory bound to the worker engine
WorkerLocalSession = sessionmaker(autocommit=False, autoflush=False, bind=get_worker_engine())


# --- Dependency for Tasks ---

def get_db_worker() -> Iterator[Session]:
    """Dependency generator for Celery tasks to yield a database session."""
    session = WorkerLocalSession()
    try:
        yield session
    finally:
        session.close()
