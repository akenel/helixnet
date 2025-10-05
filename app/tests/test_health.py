import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError  # Required to simulate a DB connection error

# Import dependencies/router components to be tested/overridden
from app.routes.health_router import health_router  # The router we are testing
from app.db.database import get_db_session  # The DB dependency we need to override

# The Celery app is imported in the router, so we mock it via patch

# 💡 Setup a minimal FastAPI app instance dedicated to testing the health router
# FIX: Renamed from 'test_app' to avoid PytestCollectionWarning.
app_instance = FastAPI()
app_instance.include_router(health_router, prefix="/health")

# --- Mocks and Fixtures Setup ---


@pytest.fixture
def client():
    """Provides a TestClient instance for running HTTP requests against the app_instance."""
    return TestClient(app_instance)


# ----------------------------------------------------------------------
# DB MOCKS (Overriding the get_db_session dependency)
# ----------------------------------------------------------------------


@pytest.fixture
def mock_db_ok_session():
    """Overrides get_db_session to simulate a successful database ping (OK status)."""

    async def override_get_db_session():
        # A mock session whose execute method returns successfully
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.execute.return_value = MagicMock()
        yield mock_session

    app_instance.dependency_overrides[get_db_session] = override_get_db_session
    yield
    # Clean up the override after the test
    app_instance.dependency_overrides.pop(get_db_session)


@pytest.fixture
def mock_db_fail_session():
    """Overrides get_db_session to simulate a database connection error (FAIL status)."""

    async def override_get_db_session():
        mock_session = MagicMock(spec=AsyncSession)
        # Mock the execute method to raise a DBAPIError, simulating connection failure
        mock_session.execute.side_effect = DBAPIError(
            "DB connection failed", {}, MagicMock()
        )
        yield mock_session

    app_instance.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app_instance.dependency_overrides.pop(get_db_session)


# ----------------------------------------------------------------------
# CELERY MOCKS (Using patch to replace the external celery_app dependency in the router)
# ----------------------------------------------------------------------


@pytest.fixture
def mock_celery_ok():
    """Mocks celery_app.control.ping to return a list of active workers (OK status)."""
    # We patch the celery_app import in the health_router module
    with patch("app.routes.health_router.celery_app.control.ping") as mock_ping:
        mock_ping.return_value = [
            {"celery@worker1": {"ok": "pong"}},
            {"celery@worker2": {"ok": "pong"}},
        ]
        yield


@pytest.fixture
def mock_celery_no_workers():
    """Mocks celery_app.control.ping to return an empty list (Broker OK, Workers FAIL)."""
    with patch("app.routes.health_router.celery_app.control.ping") as mock_ping:
        mock_ping.return_value = []
        yield


@pytest.fixture
def mock_celery_broker_down():
    """Mocks celery_app.control.ping to raise a ConnectionError (Broker FAIL)."""
    with patch("app.routes.health_router.celery_app.control.ping") as mock_ping:
        # Simulate an underlying connection error to the message broker
        mock_ping.side_effect = ConnectionError("Cannot connect to broker.")
        yield


# --- Health Check Tests ---


def test_health_check_all_ok(client, mock_db_ok_session, mock_celery_ok):
    """
    Tests the ideal scenario: both DB and Celery report OK.
    Expected: HTTP 200 OK and overall_status: OK.
    """
    response = client.get("/health/")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

    data = response.json()
    assert data["overall_status"] == "OK"

    # Verify DB check
    db_check = next(c for c in data["checks"] if c["component"] == "PostgreSQL DB")
    assert db_check["status"] == "OK"

    # Verify Celery check
    celery_check = next(c for c in data["checks"] if c["component"] == "Celery Workers")
    assert celery_check["status"] == "OK"
    assert len(celery_check["workers_online"]) == 2


def test_health_check_db_failure(client, mock_db_fail_session, mock_celery_ok):
    """
    Tests the scenario where the DB fails but Celery is OK.
    Expected: HTTP 503 Service Unavailable and overall_status: DEGRADED.
    """
    response = client.get("/health/")

    # When HTTPException 503 is raised, the response status is 503 and the body is in 'detail'
    assert response.status_code == 503, f"Expected 503, got {response.status_code}"

    data = response.json()["detail"]

    assert data["overall_status"] == "DEGRADED"

    # Verify DB check failed
    db_check = next(c for c in data["checks"] if c["component"] == "PostgreSQL DB")
    assert db_check["status"] == "FAIL"
    assert "DBAPIError" in db_check["detail"]


def test_health_check_celery_worker_failure(
    client, mock_db_ok_session, mock_celery_no_workers
):
    """
    Tests the scenario where the Celery Broker is reachable, but no workers respond.
    Expected: HTTP 503 Service Unavailable and overall_status: DEGRADED.
    """
    response = client.get("/health/")

    assert response.status_code == 503, f"Expected 503, got {response.status_code}"

    data = response.json()["detail"]

    assert data["overall_status"] == "DEGRADED"

    # Verify Celery Worker check failed
    celery_check = next(c for c in data["checks"] if c["component"] == "Celery Workers")
    assert celery_check["status"] == "FAIL"
    assert "no workers are active" in celery_check["detail"]


def test_health_check_celery_broker_failure(
    client, mock_db_ok_session, mock_celery_broker_down
):
    """
    Tests the scenario where the Celery Broker (RabbitMQ/Redis) is completely unreachable.
    Expected: HTTP 503 Service Unavailable and overall_status: DEGRADED.
    """
    response = client.get("/health/")

    assert response.status_code == 503, f"Expected 503, got {response.status_code}"

    data = response.json()["detail"]

    assert data["overall_status"] == "DEGRADED"

    # Verify Celery Broker check failed
    celery_broker_check = next(
        c for c in data["checks"] if c["component"] == "Celery Broker"
    )
    assert celery_broker_check["status"] == "FAIL"
    assert "Connection to Celery broker failed" in celery_broker_check["detail"]
    assert "ConnectionError" in celery_broker_check["detail"]
