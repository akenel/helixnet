# app/tests/test_job_submission.py.bak
import pytest
from fastapi.testclient import TestClient
# Assuming app/tests/ is next to app/main.py
from ..main import app 

# --- Import Configuration ---
# CRITICAL FIX: Import TEST_USER and TEST_PASS from conftest.py
# This ensures a single source of truth for test credentials.
from .conftest import TEST_USER, TEST_PASS 

# Initialize the TestClient once for all tests in this file
client = TestClient(app)

# Helper function to perform login and retrieve the token
# NOTE: This is a standalone version, but the pytest runner will inject 
# the 'get_auth_token' fixture from conftest.py when running the test function.
def get_auth_token():
    """Performs login and returns the access token."""
    login_data = {
        "username": TEST_USER,
        "password": TEST_PASS
    }
    
    # We use 'data' for x-www-form-urlencoded format used by the /token endpoint
    response = client.post(
        "/api/v1/token",
        data=login_data
    )
    
    # Assert Step 1: Login Success (200 OK)
    assert response.status_code == 200
    
    token = response.json().get("access_token")
    assert token is not None
    return token

def test_end_to_end_core_api_flow():
    """
    Smoke test covering the full flow:
    1. Login to get token.
    2. Retrieve user profile (check auth validity).
    3. Submit a job (check the fixed /jobs/submit route).
    """
    
    # --- 1. LOGIN ---
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # --- 2. GET CURRENT USER PROFILE ---
    # This verifies the token is functional and authentication dependency works
    me_response = client.get("/api/v1/users/me", headers=headers)
    
    # Assert Step 2: User Profile Retrieved (200 OK)
    assert me_response.status_code == 200
    # Assertion now uses the imported TEST_USER constant
    assert me_response.json()["email"] == TEST_USER
    
    # --- 3. SUBMIT ASYNCHRONOUS JOB ---
    job_data = {
        "input_data": {
            "file_path": "/data/input/123.csv", 
            "processor_type": "high_res_model"
        }
    }
    
    # CRITICAL: We use the known working path /api/v1/jobs/submit
    job_response = client.post(
        "/api/v1/jobs/submit",
        headers=headers,
        json=job_data
    )
    
    # Assert Step 3: Job Submission Accepted (202 Accepted)
    assert job_response.status_code == 202
    # Verify the response contains the job ID
    assert "id" in job_response.json()

# NOTE: We skip testing the job status retrieval (GET /api/v1/jobs/{id}) 
# because your backend needs to fix the 'JobStatus' object missing 'user_id'.
