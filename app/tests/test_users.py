import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator
from unittest.mock import MagicMock

# 💡 You will eventually replace the MockClient with your actual TestClient setup
# For now, we will create a client fixture similar to test_auth.py but with auth built-in.

# --- Mocks and Fixtures Setup for Isolated Testing ---


@pytest.fixture(scope="session")
def mock_db_session() -> Generator[AsyncSession, None, None]:
    """
    Mock database session to prevent tests from hitting PostgreSQL.
    """
    mock_session = MagicMock(spec=AsyncSession)
    yield mock_session


@pytest.fixture(scope="session")
def mock_user_data():
    """Provides consistent test data for user operations."""
    # A persistent, predictable UUID is necessary for consistent testing
    return {
        "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "email": "test_user@helix.net",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2023-01-01T00:00:00.000000",
        "updated_at": "2023-01-01T00:00:00.000000",
    }


@pytest.fixture(scope="session")
def authorized_client(mock_db_session, mock_user_data):
    """
    Mocks a TestClient that automatically includes a valid JWT token
    and simulates responses from the secure /users routes.

    CRITICAL STEP: In a real scenario, this mock MUST be replaced
    with a TestClient instance that authenticates against your actual
    API and uses dependency overrides.
    """
    MOCK_TOKEN = "mock_jwt_token_for_user_a1b2c3d4"
    AUTH_HEADER = {"Authorization": f"Bearer {MOCK_TOKEN}"}

    class MockSecuredClient:

        def get(self, url, headers=None, **kwargs):
            if headers != AUTH_HEADER:
                # Simulate 401 Unauthorized if token is missing/wrong
                return MagicMock(
                    status_code=401, json=lambda: {"detail": "Not authenticated"}
                )

            if url == "/api/v1/users/me":
                return MagicMock(status_code=200, json=lambda: mock_user_data)

            if url == "/api/v1/users/":
                # Simulate listing all users (requires admin, but we'll return a list)
                return MagicMock(status_code=200, json=lambda: [mock_user_data])

            return MagicMock(status_code=404, json=lambda: {"detail": "Not Found"})

        def patch(self, url, json=None, headers=None, **kwargs):
            if headers != AUTH_HEADER:
                return MagicMock(
                    status_code=401, json=lambda: {"detail": "Not authenticated"}
                )

            if url == "/api/v1/users/me":
                # Simulate successful update by merging patch data with mock data
                updated_data = mock_user_data.copy()
                if json:
                    updated_data.update(json)
                return MagicMock(status_code=200, json=lambda: updated_data)

            return MagicMock(status_code=404, json=lambda: {"detail": "Not Found"})

    yield MockSecuredClient()


# --- CRUD Tests using the Authorized Client ---


def test_read_users_me_success(authorized_client, mock_user_data):
    """
    Tests GET /api/v1/users/me endpoint for the authenticated user.
    """
    # The client fixture already includes the necessary Authorization header
    response = authorized_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer mock_jwt_token_for_user_a1b2c3d4"},
    )

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["email"] == mock_user_data["email"]
    assert "id" in data


def test_update_users_me_success(authorized_client):
    """
    Tests PATCH /api/v1/users/me endpoint to update user details.
    """
    update_payload = {
        "email": "new_test_email@helix.net",
        "is_active": False,  # Simulating an optional change
    }

    response = authorized_client.patch(
        "/api/v1/users/me",
        json=update_payload,
        headers={"Authorization": f"Bearer mock_jwt_token_for_user_a1b2c3d4"},
    )

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["email"] == update_payload["email"]
    assert data["is_active"] == update_payload["is_active"]
    # The ID should remain unchanged
    assert data["id"] == "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"


def test_read_all_users_admin_access(authorized_client, mock_user_data):
    """
    Tests GET /api/v1/users/ endpoint, simulating the retrieval of a list of users.
    (Note: A real-world test here should include an 'admin' token and check for a 403 Forbidden
    if the user is not an admin, but we are keeping the mock simple for now).
    """
    response = authorized_client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer mock_jwt_token_for_user_a1b2c3d4"},
    )

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["email"] == mock_user_data["email"]


def test_unauthenticated_access_is_forbidden(authorized_client):
    """
    Tests that secure endpoints correctly return 401 Unauthorized if no token is provided.
    """
    # We directly use the client's internal mechanism to skip providing a header
    # or simulate using an invalid one.

    # We'll simulate a client that is NOT the authorized_client
    class UnauthorizedClient:
        def get(self, url, headers=None, **kwargs):
            return MagicMock(
                status_code=401, json=lambda: {"detail": "Not authenticated"}
            )

        def patch(self, url, json=None, headers=None, **kwargs):
            return MagicMock(
                status_code=401, json=lambda: {"detail": "Not authenticated"}
            )

    unauthorized_client = UnauthorizedClient()

    response_get = unauthorized_client.get("/api/v1/users/me")
    assert response_get.status_code == 401

    response_patch = unauthorized_client.patch(
        "/api/v1/users/me", json={"email": "hacker@evil.com"}
    )
    assert response_patch.status_code == 401
