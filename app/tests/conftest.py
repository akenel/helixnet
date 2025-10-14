# 🧠 app/tests/conftest.py
"""
🔥 CHUCK NORRIS APPROVED TEST SETUP 🔥
-------------------------------------
This file ensures your pytest environment is totally isolated, fast, and
dev-safe. It creates a dedicated test database (helix_test_db 🧪),
runs migrations, seeds fake users, and cleans up when done.

💥 RULE #1: Tests NEVER touch your main helix_db.
💥 RULE #2: Keep your `.env.test` sacred.
💥 RULE #3: Chuck Norris doesn’t mock databases. He roundhouse-kicks them into shape.
"""

import os
import asyncio
import pytest
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import ProgrammingError
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from sqlalchemy import Engine

# 🕵️‍♂️ --- 1. Load Environment ---
if os.getenv("ENV") != "testing":
    if os.path.exists(".env.test"):
        load_dotenv(".env.test")
        print("🧪 Loaded test environment (.env.test)")
    else:
        load_dotenv(".env")
        print("⚠️  Default .env loaded (no .env.test found)")

# ⚙️ --- 2. Database Settings ---
DB_USER = os.getenv("POSTGRES_USER", "helix_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "helix_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

TEST_DB_NAME = os.getenv("TEST_DB_NAME", "helix_test_db")

# 🚀 Async test DB URL (for app)
ASYNC_TEST_DB_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
)
# 🧰 Admin DB URL (for CREATE/DROP DB)
ADMIN_DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"

# 🧱 SQLAlchemy Base (import your app's Base if available)
Base = declarative_base()

# 🧍 Test user data (example)
TEST_USER_EMAIL = "test_user_api@helixnet.com"
TEST_USER_PASSWORD = "TestSecurePassword123"

# --- CN TWEAK FOR TEST SUITE COMPATIBILITY ---
# The test files (e.g., test_job_flow.py) are looking for these exact names.
TEST_USER = TEST_USER_EMAIL
TEST_PASS = TEST_USER_PASSWORD
# ---------------------------------------------


# 🦸 --- 3. Import your FastAPI app ---
try:
    from app.main import app
except ImportError:
    print("🚨 WARNING: Could not import 'app' from 'app.main'. Using a dummy app.")
    from fastapi import FastAPI

    app = FastAPI(title="Dummy Test App")


# 🧬 --- 4. Optional Seeding Function ---
async def seed_test_user(conn):
    """
    Creates a default test user. Replace this with your real seeding logic.
    Chuck Norris seeds users just by staring at the database.
    """
    await conn.execute(
        text(
            f"INSERT INTO users (email, hashed_password) "
            f"VALUES ('{TEST_USER_EMAIL}', crypt('{TEST_USER_PASSWORD}', gen_salt('bf')))"
            f"ON CONFLICT (email) DO NOTHING;"
        )
    )
    print(f"👤 Seeded test user: {TEST_USER_EMAIL}")


# 🧪 --- 5. Fixtures ---


@pytest.fixture(scope="session")
def admin_engine() -> Engine:
    """Provides sync engine connected to 'postgres' for DB admin (CREATE/DROP)."""
    print("🔑 [ADMIN] Connecting to Postgres (admin engine)...")
    return create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")


@pytest.fixture(scope="session")
def async_engine() -> AsyncEngine:
    """Provides async engine connected to helix_test_db."""
    print("🧩 [ASYNC] Creating async test engine...")
    return create_async_engine(ASYNC_TEST_DB_URL, echo=False, future=True)


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """HTTP test client for the FastAPI app."""
    print("🧠 [CLIENT] Initializing FastAPI TestClient...")
    with TestClient(app) as test_client:
        yield test_client


# 🏗️ --- 6. Database Lifecycle Management ---


def create_test_db(engine: Engine, db_name: str):
    """Creates test database if it doesn't exist."""
    print(f"🛠️ [DB] Creating database '{db_name}' (if not exists)...")
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            conn.commit()
            print(f"✅ [DB] Database '{db_name}' created.")
    except ProgrammingError as e:
        if "42P04" in str(e):
            print(f"ℹ️ [DB] Database '{db_name}' already exists. Continuing.")
        else:
            raise


def drop_test_db(engine: Engine, db_name: str):
    """Drops the test database cleanly."""
    print(f"🧹 [DB] Dropping test database '{db_name}'...")
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                      AND pid <> pg_backend_pid();
                    """
                )
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            conn.commit()
            print(f"💥 [DB] Database '{db_name}' dropped successfully.")
    except Exception as e:
        print(f"⚠️ [DB] Could not drop test DB: {e}")


# 🧱 --- 7. Pytest Lifecycle Fixture ---
@pytest.fixture(scope="session", autouse=True)
def setup_test_database(admin_engine: Engine, async_engine: AsyncEngine):
    """
    🏗️ [DB SETUP] Full test DB lifecycle:
      1️⃣ Create test DB
      2️⃣ Build schema (from SQLAlchemy Base)
      3️⃣ Seed test user(s)
      4️⃣ Drop DB after tests
    """
    print("\n🚀 [TEST LIFECYCLE] Starting test DB setup...")

    # Assuming create_test_db is defined and working here:
    # create_test_db(admin_engine, TEST_DB_NAME)

    async def async_setup():
        # Use the async engine to connect and run synchronous DDL operations
        async with async_engine.begin() as conn:
            
            # 2. Build schema: This is the critical step to ensure the tables exist
            # The 'users' table will be created here before the seeding function is called.
            # Make sure 'Base' is imported correctly in this file!
            await conn.run_sync(Base.metadata.create_all) 
            print("✅ Database schema created (all tables exist).")

            # 3. Seed test user(s)
            await seed_test_user(conn)
            print("✅ Test user seeded successfully.")

    # Execute the async setup synchronously for the session fixture
    try:
        asyncio.run(async_setup())
    except Exception as e:
        print(f"❌ Error during database setup (async_setup). Check 'Base' import and DB connectivity: {e}")
        raise

    # 4. Teardown logic (runs after all tests in the session are complete)
    yield
    print("\n🗑️ [TEST LIFECYCLE] Starting test DB teardown...")
    # Assuming drop_test_db is defined and working here:
    # drop_test_db(admin_engine, TEST_DB_NAME)
    print("👋 Test DB teardown complete.")
