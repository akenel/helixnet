# app/tests/test_helix_api_crud.py
# --- Configuration ---
# NOTE: Set this to the address where your FastAPI service is accessible.
import pytest
import httpx
from typing import Dict, Any, Generator

# --- Configuration ---
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/users" # Assuming user endpoints are prefixed correctly

# Test User Credentials
TEST_EMAIL = "test_user_api@helixnet.com"
TEST_PASSWORD = "TestSecurePassword123"
NEW_PASSWORD = "NewSecurePassword456"

# --- Fixtures ---

# FIX: Changed scope from "session" to "module" to resolve the ScopeMismatch error.
# This ensures the fixture (and the user) is created once for this entire test file,
# which is necessary for the sequential test flow (01-05) to work.
@pytest.fixture(scope="module")
def authenticated_user_data(client: httpx.Client, setup_database) -> Generator[Dict[str, Any], None, None]:
    """
    Handles the full lifecycle of a test user using the synchronous TestClient.
    The user is created before the first test in this module and deleted after the last.
    """
    print(f"\n--- SETUP: Registering user {TEST_EMAIL} ---")

    # 1. Register the User (CREATE)
    register_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "is_active": True,
    }

    # Use POST /api/v1/users/ to create a user
    response = client.post(f"{API_PREFIX}/", json=register_payload)

    # We expect either 201 Created or 200 OK (if user already exists from a prior failed cleanup)
    if response.status_code not in [201, 200]:
        raise Exception(
            f"Failed to register test user. Status: {response.status_code}, Detail: {response.text}"
        )

    user_data = response.json()
    created_user_id = user_data.get("id")

    print(f"User created with ID: {created_user_id}")

    # 2. Log in and get token
    login_payload = {"username": TEST_EMAIL, "password": TEST_PASSWORD}
    # Use POST /api/v1/token for login (assuming the standard /token endpoint)
    token_response = client.post(
        "/api/v1/token",
        data=login_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert (
        token_response.status_code == 200
    ), f"Failed to authenticate: {token_response.text}"
    token_data = token_response.json()
    token = token_data.get("access_token")

    if not created_user_id:
        # Fallback check if registration returned 200 (user pre-existed)
        # We need to fetch the ID for cleanup
        user_me_response = client.get(
            f"{API_PREFIX}/me", headers={"Authorization": f"Bearer {token}"}
        )
        created_user_id = user_me_response.json().get("id")

    yield {"user_id": created_user_id, "token": token, "email": TEST_EMAIL}

    # 4. Teardown: Delete the user
    print(f"\n--- TEARDOWN: Deleting user {created_user_id} ---")

    # We must delete the user using the token
    cleanup_response = client.delete(
        f"{API_PREFIX}/{created_user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    # Expect 204 No Content for successful deletion or 404 if the user was already deleted
    assert cleanup_response.status_code in [204, 404]
    print("User successfully deleted.")


# --- Tests (Synchronous) ---

def test_01_read_current_user_me(
    client: httpx.Client, authenticated_user_data: Dict[str, Any]
):
    """
    Tests GET /api/v1/users/me (READ operation) using the token fixture.
    """
    user_id = authenticated_user_data["user_id"]
    token = authenticated_user_data["token"]

    print(f"Testing GET {API_PREFIX}/me for user {user_id}")

    response = client.get(
        f"{API_PREFIX}/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == TEST_EMAIL
    print("Test 01 (Read Me) passed.")


def test_02_read_user_by_id(
    client: httpx.Client, authenticated_user_data: Dict[str, Any]
):
    """
    Tests GET /api/v1/users/{user_id} (READ operation).
    """
    user_id = authenticated_user_data["user_id"]
    token = authenticated_user_data["token"]

    print(f"Testing GET {API_PREFIX}/{user_id}")

    response = client.get(
        f"{API_PREFIX}/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    print("Test 02 (Read by ID) passed.")


def test_03_update_user_patch(
    client: httpx.Client, authenticated_user_data: Dict[str, Any]
):
    """
    Tests PATCH /api/v1/users/{user_id} (UPDATE operation).
    """
    user_id = authenticated_user_data["user_id"]
    token = authenticated_user_data["token"]

    new_email = "updated_test_email@helixnet.com"
    update_payload = {"email": new_email, "password": NEW_PASSWORD, "is_active": False}

    print(f"Testing PATCH {API_PREFIX}/{user_id}")

    response = client.patch(
        f"{API_PREFIX}/{user_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check if the email and active status were updated
    assert data["email"] == new_email
    assert data["is_active"] is False
    print("Test 03 (Update) passed.")


def test_04_read_all_users_pagination(
    client: httpx.Client, authenticated_user_data: Dict[str, Any]
):
    """
    Tests GET /api/v1/users/?skip=0&limit=100 (READ ALL operation).
    Verifies the newly created user is in the list.
    """
    user_id = authenticated_user_data["user_id"]
    token = authenticated_user_data["token"]

    print(f"Testing GET {API_PREFIX}/ (Read All)")

    response = client.get(
        f"{API_PREFIX}/?skip=0&limit=10", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check if the response is a list
    assert isinstance(data, list)

    # Check if the test user is present in the list (or at least one user)
    assert any(user.get("id") == user_id for user in data)
    print("Test 04 (Read All) passed.")


def test_05_cleanup_and_delete(
    client: httpx.Client, authenticated_user_data: Dict[str, Any]
):
    """
    Tests DELETE /api/v1/users/{user_id} (DELETE operation) explicitly.
    Verifies a 404 NOT FOUND after an explicit DELETE attempt.
    """
    user_id = authenticated_user_data["user_id"]
    token = authenticated_user_data["token"]

    print(f"Testing DELETE {API_PREFIX}/{user_id}")

    # Explicitly delete the user (will be harmless if the fixture already ran cleanup)
    delete_response = client.delete(
        f"{API_PREFIX}/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    # Expect 204 No Content for a successful deletion or 404 if the fixture already deleted it
    assert delete_response.status_code in [204, 404]

    # Try to read the user again, expecting a 404
    read_response = client.get(
        f"{API_PREFIX}/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    # Expect 404 Not Found after deletion
    assert read_response.status_code == 404
    print("Test 05 (Delete/Cleanup verification) passed.")

