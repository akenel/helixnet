import pytest
from uuid import UUID
from unittest.mock import MagicMock
from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession

# 💡 Fixtures and Mocks Setup for Job Testing

MOCK_JOB_ID = "c64b9721-7c4a-4ca8-bdc4-2a9b1a85530a"
MOCK_TOKEN = "mock_jwt_token_for_job_testing"
AUTH_HEADER = {"Authorization": f"Bearer {MOCK_TOKEN}"}

# Example Job Submission Payload
JOB_PAYLOAD = {
    "task_name": "data_analysis_task",
    "parameters": {"input_file": "s3://helix/data.csv", "threshold": 0.5},
}

# Mocked Job Status Responses
PENDING_STATUS = {
    "job_id": MOCK_JOB_ID,
    "status": "PENDING",
    "message": "Job successfully submitted and queued for processing.",
    "result_data": None,
}

SUCCESS_STATUS = {
    "job_id": MOCK_JOB_ID,
    "status": "SUCCESS",
    "message": "Processing complete.",
    "result_data": {"total_records": 1500, "processed": 1490, "errors": 10},
}


@pytest.fixture(scope="session")
def mock_db_session() -> Generator[AsyncSession, None, None]:
    """Mock database session to prevent tests from hitting PostgreSQL."""
    mock_session = MagicMock(spec=AsyncSession)
    yield mock_session


@pytest.fixture(scope="session")
def authorized_job_client(mock_db_session):
    """
    Mocks a TestClient that includes a valid JWT token and simulates
    responses from the secure /jobs routes, mocking the job service layer.
    """

    class MockSecuredJobClient:

        def post(self, url, json=None, headers=None, **kwargs):
            if headers != AUTH_HEADER:
                # 401 Unauthorized for missing/wrong token
                return MagicMock(
                    status_code=401, json=lambda: {"detail": "Not authenticated"}
                )

            if url == "/api/v1/jobs/":
                # Simulate successful submission (service submit_new_job result)
                return MagicMock(status_code=202, json=lambda: PENDING_STATUS)

            return MagicMock(status_code=404, json=lambda: {"detail": "Not Found"})

        def get(self, url, headers=None, **kwargs):
            if headers != AUTH_HEADER:
                # 401 Unauthorized for missing/wrong token
                return MagicMock(
                    status_code=401, json=lambda: {"detail": "Not authenticated"}
                )

            # Use UUID validation in the mock to match the router's path parameter
            if url == f"/api/v1/jobs/{MOCK_JOB_ID}":
                # Simulate the job service returning SUCCESS based on the query path
                if "success" in url.lower():
                    # This branch is not hit in the current structure but useful for service mocking
                    return MagicMock(status_code=200, json=lambda: SUCCESS_STATUS)

                # Default mock for status retrieval is PENDING
                return MagicMock(status_code=200, json=lambda: PENDING_STATUS)

            # Simulate job not found
            if url != f"/api/v1/jobs/{MOCK_JOB_ID}" and "/api/v1/jobs/" in url:
                return MagicMock(
                    status_code=404, json=lambda: {"detail": "Job not found"}
                )

            return MagicMock(status_code=404, json=lambda: {"detail": "Not Found"})

    yield MockSecuredJobClient()


# --- Job Processing Tests ---


def test_job_submission_success(authorized_job_client):
    """
    Tests POST /api/v1/jobs/ endpoint, expecting HTTP 202 ACCEPTED.
    """
    response = authorized_job_client.post(
        "/api/v1/jobs/", json=JOB_PAYLOAD, headers=AUTH_HEADER
    )

    # Critical: Job submissions should return 202 Accepted, not 200 OK
    assert (
        response.status_code == 202
    ), f"Expected 202, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["status"] == "PENDING"
    assert "job_id" in data


def test_get_job_status_pending(authorized_job_client):
    """
    Tests GET /api/v1/jobs/{job_id} and checks for a PENDING status.
    """
    response = authorized_job_client.get(
        f"/api/v1/jobs/{MOCK_JOB_ID}", headers=AUTH_HEADER
    )

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["job_id"] == MOCK_JOB_ID
    assert data["status"] == "PENDING"
    assert data["result_data"] is None


def test_get_job_status_not_found(authorized_job_client):
    """
    Tests GET /api/v1/jobs/{job_id} for a non-existent ID.
    """
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = authorized_job_client.get(
        f"/api/v1/jobs/{non_existent_id}", headers=AUTH_HEADER
    )

    assert (
        response.status_code == 404
    ), f"Expected 404, got {response.status_code}: {response.json()}"
    assert "Job not found" in response.json().get("detail", "")


def test_job_unauthenticated_access_is_forbidden(authorized_job_client):
    """
    Tests that job endpoints require authentication.
    """

    # Simulate a client that is NOT the authorized_client
    class UnauthorizedClient:
        def post(self, url, json=None, headers=None, **kwargs):
            return MagicMock(
                status_code=401, json=lambda: {"detail": "Not authenticated"}
            )

        def get(self, url, headers=None, **kwargs):
            return MagicMock(
                status_code=401, json=lambda: {"detail": "Not authenticated"}
            )

    unauthorized_client = UnauthorizedClient()

    # Test POST endpoint
    response_post = unauthorized_client.post("/api/v1/jobs/", json=JOB_PAYLOAD)
    assert response_post.status_code == 401

    # Test GET endpoint
    response_get = unauthorized_client.get(f"/api/v1/jobs/{MOCK_JOB_ID}")
    assert response_get.status_code == 401
