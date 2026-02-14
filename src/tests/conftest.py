# tests/conftest.py
"""
Shared fixtures for Camper & Tour test suite.
Uses SQLite in-memory DB for speed and isolation.
Maps PostgreSQL-specific types (JSONB, enums) to SQLite equivalents.
"""
import pytest
import pytest_asyncio
from sqlalchemy import event, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from src.db.models.base import Base


# Map JSONB -> JSON for SQLite (JSONB is PostgreSQL-only)
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """SQLite in-memory engine, created once per test session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, future=True
    )

    # SQLite doesn't enforce FK constraints by default
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db_engine):
    """Fresh DB session per test. Creates all tables, yields session, drops all."""
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(
        test_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
    # Drop all tables (ignore FK cycle errors in SQLite)
    try:
        async with test_db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        # SQLite can't resolve circular FK deps on DROP -- safe to ignore
        # since in-memory DB is per-session and tables get recreated per test
        pass
