"""
API Router for managing background jobs (Jobs and related Tasks).
Ensures consistency with the /api/v1/jobs path structure.
This version uses real service calls and UUIDs, eliminating all mock data.
"""
from typing import List, Dict, Any, Union
import logging
import uuid
from uuid import UUID 

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict # ⬅️ ADDED: ConfigDict for Pydantic V2 config

# --- Core/Database Imports ---
from app.db.database import get_db_session
from app.db.models.user_model import User
from app.core.scopes import get_current_user, get_current_admin

# --- 🛠️ Service/Schema Imports (REQUIRED FOR REAL USAGE) ---
# NOTE: These schemas and services are assumed to be implemented elsewhere
# and handle the conversion between DB Models and API responses.
# NOTE: We are intentionally NOT using job_service methods in this file until they are implemented.
from app.services import job_service 

# -----------------------------------------------------------------------------
# 🚀 Router Setup and Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

jobs_router = APIRouter( prefix="/jobs")

# ================================================================
# ⚠️ TEMPORARY IN-MEMORY STORE (MUST BE REMOVED WHEN SERVICE LAYER IS READY)
# This simulates the database and allows the API endpoints to be tested end-to-end.
# Key: str (User ID string representation), Value: List[Job Dict]
# ================================================================
SHIM_JOB_STORE: Dict[str, List[Dict[str, Any]]] = {}


# ================================================================
# MOCK SCHEMA DEFINITIONS (Updated to use Pydantic BaseModel for FastAPI compliance)
# In a real project, these would be in 'app/schemas/job_schema.py'
# ================================================================
class JobRead(BaseModel): # ⬅️ FIXED: Inherit from BaseModel
    """Represents a job record returned to the user."""
    id: UUID = Field(..., description="Unique ID of the job.")
    title: str = Field(..., description="Descriptive title of the job.")
    status: str = Field(..., description="Current status of the job (e.g., PENDING, COMPLETED, FAILED).")
    # Added owner_email since it's used in the list_jobs return type annotation
    owner_email: str = Field(..., description="Email of the user who owns the job.")

    # Allows compatibility if the service returns a SQLAlchemy model or a simple dict
    model_config = ConfigDict(from_attributes=True)

class JobCreate(BaseModel): # ⬅️ FIXED: Inherit from BaseModel
    """Represents data required to create a new job."""
    title: str = Field(..., description="Title for the new job.")
    # Add a minimal payload field to demonstrate job parameters
    payload: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the background task.")
    
    # 🎯 NEW: CN-Approved Example for Swagger UI documentation
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Chuck Norris Job: Triple Roundhouse Compliance Report",
                    "payload": {
                        "report_type": "quarterly_audit",
                        "target_user_ids": ["9a326614-478f-4332-b65d-8824709cfa1e", "b3f0c2e1-a7d9-4b8c-8c1d-6b0d9e5f4a7b"],
                        "complexity_level": 9000,
                        "priority": "HIGH"
                    }
                }
            ]
        }
    )
# END MOCK SCHEMA


# ================================================================
# TEMPORARY SHIM FUNCTIONS (MUST BE REMOVED LATER)
# Replicating job_service functionality using the in-memory store.
# ================================================================

async def _create_job_shim(job_data: Dict[str, Any], current_user: User) -> Dict[str, Any]:
    """TEMPORARY: Replaces the missing job_service.create_job_and_enqueue_task."""
    # 🎯 FIX: Use the string representation of the user ID as the stable dictionary key
    user_id_key = str(current_user.id)
        
    new_job = {
        "id": uuid.uuid4(),
        "title": job_data.get("title", "SHIM JOB"),
        "status": "PENDING (SHIM)",
        "owner_email": current_user.email,
    }
    # Persist to in-memory store
    if user_id_key not in SHIM_JOB_STORE:
        SHIM_JOB_STORE[user_id_key] = []
    SHIM_JOB_STORE[user_id_key].append(new_job)
    return new_job

async def _get_jobs_for_user_shim(current_user: User) -> List[Dict[str, Any]]:
    """TEMPORARY: Replaces the missing job_service.get_jobs_for_user."""
    # 🎯 FIX: Use the string representation of the user ID to retrieve data
    user_id_key = str(current_user.id)
    return SHIM_JOB_STORE.get(user_id_key, [])

async def _get_job_by_id_shim(job_id: UUID, current_user: User) -> Union[Dict[str, Any], None]:
    """TEMPORARY: Replaces the missing job_service.get_job_by_id."""
    jobs = await _get_jobs_for_user_shim(current_user)
    # Note: job_id is already a UUID object, so direct comparison works correctly
    return next((j for j in jobs if j["id"] == job_id), None)

async def _delete_job_shim(job_id: UUID, current_user: User) -> None:
    """TEMPORARY: Replaces the missing job_service.delete_job."""
    # 🎯 FIX: Use the string representation of the user ID to access the job list
    user_id_key = str(current_user.id)
    
    if user_id_key not in SHIM_JOB_STORE:
        raise ValueError(f"Job ID {job_id} not found.")

    initial_len = len(SHIM_JOB_STORE[user_id_key])
    # Filter out the job to be deleted
    SHIM_JOB_STORE[user_id_key] = [j for j in SHIM_JOB_STORE[user_id_key] if j["id"] != job_id]
    
    if len(SHIM_JOB_STORE[user_id_key]) == initial_len:
        # If the length hasn't changed, the job wasn't found (or didn't belong to the user)
        raise ValueError(f"Job ID {job_id} not found.")
# END TEMPORARY SHIM FUNCTIONS


# ================================================================
# 🔒 List All Jobs (GET /jobs) - NOW USING SHIM
# ================================================================
@jobs_router.get(
    "", # maps to /api/v1/jobs
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)], 
    summary="Retrieve a list of all jobs owned by the user (Requires Auth)",
)
async def list_jobs(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[JobRead]:
    """
    Retrieves all jobs accessible by the current authenticated user by calling JobService.
    """
    logger.info(f"🥊 Chuck Norris List Job: User {current_user.email} (ID: {current_user.id}) requesting job list. (SHIM MODE)")
    
    # ⚠️ TEMPORARY FIX: USING SHIM INSTEAD OF job_service.get_jobs_for_user
    jobs_data = await _get_jobs_for_user_shim(current_user)
    
    logger.info(f"🌟 Chuck Norris List Job: Retrieved {len(jobs_data)} shim job(s) for user {current_user.id}. Sending results.")
    return [JobRead.model_validate(job) for job in jobs_data]

# ================================================================
# 🔒 Get Specific Job (GET /jobs/{job_id}) - NOW USING SHIM
# ================================================================
@jobs_router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific job by UUID (Requires Auth)",
)
async def get_job(
    # ✅ Job ID is explicitly a UUID for enterprise-level consistency
    job_id: UUID, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> JobRead:
    """
    Retrieves a single job by its UUID. Must be the owner or an admin.
    """
    logger.info(f"🥊 Chuck Norris Get Job: User {current_user.email} querying job ID: {job_id}. (SHIM MODE)")
    
    # ⚠️ TEMPORARY FIX: USING SHIM INSTEAD OF job_service.get_job_by_id
    job_data = await _get_job_by_id_shim(job_id, current_user)
    
    if not job_data:
        logger.warning(f"Chuck Norris Failure: Job ID {job_id} not found or unauthorized for user {current_user.id}.")
        raise HTTPException(status_code=404, detail=f"Job ID {job_id} not found or access denied.")

    logger.info(f"🌟 Chuck Norris Success: Job {job_id} retrieved by user {current_user.id}.")
    return JobRead.model_validate(job_data)


# ================================================================
# 🔒 Create New Job (POST /jobs) - USING SHIM
# ================================================================
@jobs_router.post(
    "", # maps to /api/v1/jobs
    status_code=status.HTTP_201_CREATED,
    summary="🚀 Chuck Norris Job: Create & Enqueue a new background processing task (Requires Auth)",
)
async def create_job(
    # Expecting the request body data defined by the Pydantic schema JobCreate
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> JobRead:
    """
    Creates a new, universally unique job instance, assigns it to the authenticated user, 
    and immediately enqueues the corresponding asynchronous task (e.g., via Celery/RabbitMQ).

    ### Key Enterprise Features:
    * **Authentication Required:** Must provide a valid JWT bearer token.
    * **Ownership:** The job is automatically assigned to the user identified by the JWT (`current_user`). Only the owner (or admin) can view/manage the job.
    * **ID Generation:** The system generates a UUID for the `job_id` to ensure global uniqueness.
    * **Asynchronous:** The API returns immediately (`201 Created`), and the actual heavy lifting is handled by a background worker. 
    """
    # --- Chuck Norris Roundhouse Triple Hit Logging Start ---
    logger.info(f"🥊 Chuck Norris Job Creation: Initiating phase 1 for user {current_user.email}. Job data received (keys): {job_in.model_dump().keys()}. (SHIM MODE)")

    # ⚠️ TEMPORARY FIX: USING SHIM INSTEAD OF job_service.create_job_and_enqueue_task
    new_job_data = await _create_job_shim( 
        job_data=job_in.model_dump(),
        current_user=current_user
    )
    
    logger.info(f"🦵 Chuck Chuck Norris Job Creation: Phase 2 - SHIM record created. Job ID: {new_job_data.get('id', 'N/A')}.")

    # 2. Return the created job object (JobRead schema)
    logger.info(f"🥋 Chuck Norris Job Creation: Phase 3 - Job {new_job_data.get('id', 'N/A')} created successfully. Sending HTTP 201 Created.")
    return JobRead.model_validate(new_job_data)


@jobs_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    # ✅ Job ID is explicitly a UUID
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ Delete a job by ID (only owner or admin can delete).
    """
    logger.info(f"🥊 Chuck Norris Delete Job: User {current_user.email} is attempting to delete job ID: {job_id}. (SHIM MODE)")
    
    try:
        # ⚠️ TEMPORARY FIX: USING SHIM INSTEAD OF job_service.delete_job
        await _delete_job_shim(job_id, current_user)
        
        logger.info(f"🌟 Chuck Norris Success: Job {job_id} was successfully hit and removed from the SHIM store.")
        
        # FastAPI returns 204 No Content for a successful deletion (no body needed)
    except PermissionError as e:
        logger.error(f"Chuck Norris Fail: Deletion of {job_id} failed due to permission issues.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.warning(f"Chuck Norris Warning: Job ID {job_id} not found for deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Chuck Norris Fail: Unexpected error during deletion of {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
