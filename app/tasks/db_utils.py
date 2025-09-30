"""
Database utilities specifically for Celery tasks.

Provides a database session function compatible with Celery's 
task execution context.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc # Imported for robust error handling

# We import SessionLocal (which is an AsyncSession factory) and the engine.
from app.db.database import SessionLocal, engine 

# Note the 'async def' keyword and 'AsyncGenerator' return type
async def get_celery_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async database session suitable for use within a 
    Celery task, managing connection and closing using the context manager.
    """
    # CRITICAL: Use 'async with' when dealing with the AsyncSession factory
    async with SessionLocal() as session:
        try:
            yield session
        except exc.SQLAlchemyError:
            # Rollback any pending changes if an exception occurs
            await session.rollback()
            raise
        # The context manager automatically handles session closing
        # after the yield block is exited.
