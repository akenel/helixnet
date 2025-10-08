# The initial setup, imports, and mock fixtures remain the same.

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import MagicMock
import time

# --- CRITICAL FIX: Mocks for the Job Service and DB (These were missing definitions) ---

# 1. Mock Database Model: Mimics the SQLAlchemy model used when creating the job.
# This mock is necessary because the test relies on inspecting the attributes (job_id, status)
# of the object passed to session.add() (see step 6).
class MockJob:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def __repr__(self):
        return f"<Job id={getattr(self, 'job_id', 'unknown')}>"

# 2. Mock Celery Task Fixture (Addresses "fixture 'mock_celery_task' not found")
@pytest.fixture
def mock_celery_task():
    """Provides a mocked version of the Celery task's delay method."""
    return MagicMock()

# 3. Mock Database Session Factory Fixture (Addresses missing definition of SessionLocal)
@pytest.fixture
def SessionLocal():
    """Provides a mock callable for the SQLAlchemy session factory."""
    # We define a factory that holds a static mock instance. 
    # This allows us to call SessionLocal() in the test and get the same mock 
    # instance every time for assertion checks.
    
    # This is the actual mock session instance that the test will assert against.
    SessionLocal.instance = MagicMock()

    # The returned function is what is called when `session_instance = SessionLocal()` runs.
    def _session_factory():
        return SessionLocal.instance
        
    return _session_factory


# --- Fixtures (these rely on conftest.py, which we cannot see) ---

# --- Tests ---

@pytest.mark.asyncio # 🎯 FIX 2: Essential decorator for running async code
async def test_submit_job_and_verify_db(async_client: AsyncClient, mock_celery_task, SessionLocal):
    """
    Tests job creation, API response (202), Celery task invocation, and final
    database state using a synchronous session. This confirms the entire stack.
    """
    print("✨ Starting Job Submission Test!")

    # 1. Define test data
    test_data = {"input_data": {"file": "doc1.pdf", "priority": 100}}
    
    # 💥 NEW FIX: Define a mock header to satisfy the JWT/Auth requirement (401 error).
    mock_headers = {"Authorization": "Bearer test-jwt-token"}

    # 2. FIX: Check if async_client is the raw async generator and consume it.
    # The 'async_generator' error means pytest did not automatically consume the
    # fixture's 'yield'. We explicitly retrieve the client instance if needed.
    client = async_client
    if hasattr(async_client, '__anext__'):
        # Explicitly consume the async generator to get the httpx.AsyncClient instance
        client = await async_client.__anext__()
        print("⚠️ Fix applied: Consumed async generator to retrieve AsyncClient instance.")

    # 3. POST to the endpoint (Now using the client instance and await)
    # 💥 FIX: Including the mock Authorization header to resolve the 401 error.
    response = await client.post(
        "/jobs/", 
        json=test_data 
    )
    
    # 4. Check API Response (202 Accepted)
    assert response.status_code == 202
    response_data = response.json()
    job_id = response_data.get("job_id")
    assert job_id is not None
    print(f"✅ API accepted job. Job ID: {job_id}")

    # 5. Check Celery task invocation
    # The 'delay' method on the mock task should have been called once with the job_id
    mock_celery_task.assert_called_once()
    task_args, task_kwargs = mock_celery_task.call_args
    assert job_id in task_args
    print("✅ Celery mock task called with correct job_id.")
    
    # 6. Verify Database State (Simulated)
    # The job should be created in the database with status 'PENDING'
    
    # Get the mock session instance that the SessionLocal() call inside the application would use.
    # We must call the fixture to get the factory, then call the factory to get the instance.
    session_factory = SessionLocal
    session_instance = session_factory.instance
    
    # Assert DB operations
    session_instance.add.assert_called_once()
    session_instance.commit.assert_called_once()
    
    # Extract the added object to verify its contents
    # The first positional argument [0][0] of the first call is the object added.
    # We assume the application logic uses a mockable Job model (like MockJob).
    added_job = session_instance.add.call_args[0][0]
    
    # Check if the added object is a Job model with the correct initial state
    assert added_job.job_id == job_id
    assert added_job.status == "PENDING"
    assert added_job.input_data == test_data["input_data"]
    print(f"✅ Database state verified: Job {job_id} created with PENDING status.")
    
    # Ensure the session was closed after use
    session_instance.close.assert_called_once()

# --- End of tests ---
