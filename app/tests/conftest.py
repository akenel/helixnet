import pytest
import asyncio
from typing import Generator, Dict, Any
import httpx
from datetime import timedelta
import logging
import uuid

from sqlalchemy.orm import Session
from app.db.database import get_db_session, get_db_session_sync, SyncEngine, Base
from app.core.config import get_settings
from app.services.user_service import (
    get_password_hash,
)  # Used for hashing test user password
from app.core.security import create_access_token  # Used to generate the test JWT token
from app.db.models.user import User as UserModel  # Import the SQLAlchemy Model

# --- 1. SETUP & CONSTANTS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants inferred to be used by the test file (test_helix_api_crud.py)
TEST_EMAIL = "test_crud_user@helix.net"
TEST_PASSWORD = "testpassword123"
# Retrieve the configured API prefix from settings
API_PREFIX = get_settings().API_V1_STR

# FIX: Import the FastAPI application object for testing
try:
    from app.main import app
except ImportError:
    logger.error(
        "Could not import 'app' from app.main. Ensure app/main.py exports the FastAPI instance."
    )
    raise


# --- 2. CORE DATABASE FIXTURES (Sync/Async Setup) ---


@pytest.fixture(scope="session")
def sync_engine():
    """Provides the synchronous SQLAlchemy engine for session-level setup/teardown."""
    return SyncEngine


@pytest.fixture(scope="session", autouse=True)
def setup_database(sync_engine):
    """
    Sets up the test database schema before the session and drops it after.
    This ensures a clean database for every test run.
    """
    logger.info("Initializing test database structure...")
    Base.metadata.create_all(bind=sync_engine)
    yield
    logger.info("Cleaning up and dropping test database structure...")
    Base.metadata.drop_all(bind=sync_engine)


@pytest.fixture(scope="function")
def sync_db_session() -> Generator[Session, None, None]:
    """
    Provides a synchronous database session for test setup/data insertion.
    This fixture ensures a clean session that is rolled back after each test.
    """
    # Use the context manager defined in database.py
    with get_db_session_sync() as session:
        yield session
        # Explicit rollback for safety, even though the context manager should handle it.
        session.rollback()


# --- 3. OVERRIDE DEPENDENCIES FOR ASYNC TESTING (Function Scope) ---


@pytest.fixture(scope="function")
def override_get_db_session(sync_db_session: Session):
    """
    Overrides the FastAPI dependency (get_db_session) to use the synchronous
    test session for test isolation and transaction control.
    (Function scoped to ensure it's set/cleared for every test).
    """

    async def _get_test_session():
        # FastAPI expects an async generator, so we wrap the sync session yield.
        yield sync_db_session

    # Apply the override
    app.dependency_overrides[get_db_session] = _get_test_session
    yield

    # Cleanup the override after the test
    app.dependency_overrides.clear()


# --- 4. HTTP CLIENT FIXTURE (Function Scope) ---


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Overrides the pytest-asyncio default event loop to be session-scoped."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")  # <-- FIX: Changed scope from 'session' to 'function'
async def async_client(override_get_db_session) -> httpx.AsyncClient:
    """
    Provides an asynchronous HTTP client configured to talk to the FastAPI app,
    ensuring our overridden database dependency is active.
    (Function scoped to align with override_get_db_session).
    """
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# --- 5. AUTHENTICATION FIXTURE (Function Scope) ---


@pytest.fixture(scope="function")
def authenticated_user_data(
    sync_db_session: Session,
) -> Generator[Dict[str, Any], None, None]:
    """
    Creates a temporary test user in the database, generates a valid JWT token
    for them, yields the authentication data, and deletes the user afterward.
    (Function scoped to ensure a clean user is created/deleted for every test).
    """
    logger.info("Setting up authenticated_user_data fixture...")

    # 1. Create a clean test user
    hashed_password = get_password_hash(TEST_PASSWORD)
    test_user_id = uuid.uuid4()

    user_model = UserModel(
        id=test_user_id,
        email=TEST_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
    )

    sync_db_session.add(user_model)
    sync_db_session.commit()
    sync_db_session.refresh(user_model)
    logger.info(f"Test user created successfully: ID={user_model.id}")

    # 2. Generate the JWT authentication token
    to_encode = {"sub": str(user_model.id), "email": user_model.email}
    access_token = create_access_token(
        data=to_encode, expires_delta=timedelta(minutes=5)
    )

    user_data = {
        "user_id": str(user_model.id),
        "email": TEST_EMAIL,
        "token": access_token,
    }

    # 3. Yield the data to the tests that request this fixture
    yield user_data

    # 4. Teardown: Clean up the user after the test run is complete
    logger.info(f"Tearing down test user: ID={user_data['user_id']}")
    try:
        user_to_delete = (
            sync_db_session.query(UserModel)
            .filter(UserModel.id == user_model.id)
            .first()
        )
        if user_to_delete:
            sync_db_session.delete(user_to_delete)
            sync_db_session.commit()
    except Exception as e:
        logger.error(f"Failed to clean up test user {user_data['user_id']}: {e}")
        sync_db_session.rollback()
