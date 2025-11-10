# tests/conftest.py
import os
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import src
from src.main import app   # Your FastAPI app
from src.db.models.base import Base
from src.db.database import get_db_session


# 🧪 Create a temporary SQLite in-memory DB for tests
@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    return engine


# ⚙️ Create a new session per test
@pytest.fixture(scope="function")
async def db_session(test_db_engine):
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = sessionmaker(
        test_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 🔌 Dependency override for FastAPI to use the test DB
@pytest.fixture(scope="function", autouse=True)
def override_get_db_session(db_session):
    src.dependency_overrides[get_db_session] = lambda: db_session
    yield
    src.dependency_overrides.clear()


# 🚀 Async test client
@pytest.fixture(scope="function")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
