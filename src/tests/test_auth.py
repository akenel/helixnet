import pytest

# The TestClient is the standard way to test FastAPI endpoints
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator
from unittest.mock import MagicMock

# 💡 IMPORTANT: You must import your actual FastAPI app instance and dependencies here.
# Assuming: from src.main import app
# Assuming: from src.db.database import get_db_session

# --- Fixtures and Mocks (Minimal Test Environment Setup) ---


@pytest.fixture(scope="module")
def mock_db_session() -> Generator[AsyncSession, None, None]:
    """
    Fixture to mock the database session for dependency override.
    This prevents tests from hitting the live PostgreSQL database.
    """
    mock_session = MagicMock(spec=AsyncSession)
    yield mock_session


# NOTE: In a real project, this entire setup would move to a 'conftest.py' file.
@pytest.fixture(scope="module")
def client(mock_db_session):
    """
    Provides a TestClient instance for making API requests with dependencies mocked.

    CRITICAL STEP: Replace the following MockAppClient with your actual setup:
    1. Import your 'app' instance (e.g., from src.main import app).
    2. Override dependencies (e.g., dependency_overrides[get_db_session] = override_function).
    3. Instantiate TestClient(app).
    """

    # --- START OF MOCK CLIENT (REPLACE THIS BLOCK) ---
    class MockAppClient:
        # Simulate a successful login logic defined in app/services/user_service.py
        def post(self, url, data=None, json=None, headers=None):
            if url == "/api/v1/token":
                if (
                    data
                    and data.get("username") == "test@helix.net"
                    and data.get("password") == "test"
                ):
                    return MagicMock(
                        status_code=200,
                        json=lambda: {
                            "access_token": "mock_jwt_token",
                            "token_type": "bearer",
                        },
                    )
                # Simulate failure response for bad credentials
                return MagicMock(
                    status_code=400,
                    json=lambda: {"detail": "Incorrect username or password"},
                )

            # Placeholder for other posts
            return MagicMock(status_code=404)

        def get(self, url, headers=None):
            # Placeholder for GET requests
            return MagicMock(status_code=404)

    yield MockAppClient()
    # --- END OF MOCK CLIENT (REPLACE THIS BLOCK) ---


# --- Authentication Tests ---


def test_get_access_token_success(client):
    """
    Tests successful retrieval of an access token using correct credentials.
    The response must contain 'access_token' and 'token_type: bearer'.
    """
    # Standard OAuth2 login requires 'username' and 'password' in form data (data=...)
    login_data = {"username": "test@helix.net", "password": "test"}

    # We are assuming your login endpoint is at the standard /api/v1/token path
    response = client.post("/api/v1/token", data=login_data)

    assert response.status_code == 200, (
        f"Expected HTTP 200 for successful login, but got {response.status_code}. "
        f"Response: {response.json()}"
    )

    response_json = response.json()
    assert "access_token" in response_json
    assert response_json["token_type"] == "bearer"


def test_get_access_token_failure_bad_password(client):
    """
    Tests failure when providing an incorrect password.
    """
    login_data = {"username": "test@helix.net", "password": "wrong_password"}

    response = client.post("/api/v1/token", data=login_data)

    # Failure should result in 400 (Bad Request) or 401 (Unauthorized)
    assert (
        response.status_code == 400 or response.status_code == 401
    ), f"Expected HTTP 400/401 for failed login, but got {response.status_code}."


def test_get_access_token_failure_bad_username(client):
    """
    Tests failure when providing a non-existent username (email).
    """
    login_data = {"username": "non_existent@helix.net", "password": "any_password"}

    response = client.post("/api/v1/auth/token", data=login_data)

    # Failure should result in 400 (Bad Request) or 401 (Unauthorized)
    assert (
        response.status_code == 400 or response.status_code == 401
    ), f"Expected HTTP 400/401 for failed login, but got {response.status_code}."
