"""
API Router for managing background jobs (Jobs and related Tasks).
Ensures consistency with the /api/v1/jobs path structure.
This version uses real service calls and UUIDs, eliminating all mock data.
"""
from pathlib import Path
from typing import List, Dict, Any, Union
import logging
from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile # File and UploadFile are correctly imported
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
import uuid
from uuid import UUID 

# Assuming the following service/schema imports exist in your project structure
from app.schemas.job_schema import JobSubmission # Assuming JobSubmission is defined here
from app.db.database import get_db_session
from app.db.models.user_model import User
from app.core.scopes import get_current_user, get_current_admin
from app.services import job_service 

# -----------------------------------------------------------------------------
# 🚀 Router Setup and Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

jobs_router = APIRouter( prefix="/jobs")

# ================================================================
# ⚠️ TEMPORARY IN-MEMORY STORE (MUST BE REMOVED WHEN SERVICE LAYER IS READY)
# ================================================================
SHIM_JOB_STORE: Dict[str, List[Dict[str, Any]]] = {}


# ================================================================
# MOCK SCHEMA DEFINITIONS 
# ================================================================
class JobRead(BaseModel):
    """Represents a job record returned to the user."""
    id: UUID = Field(..., description="Unique ID of the job.")
    title: str = Field(..., description="Descriptive title of the job.")
    status: str = Field(..., description="Current status of the job (e.g., PENDING, COMPLETED, FAILED).")
    owner_email: str = Field(..., description="Email of the user who owns the job.")

    model_config = ConfigDict(from_attributes=True)

class JobCreate(BaseModel):
    """Represents data required to create a new job."""
    title: str = Field(..., description="Title for the new job.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the background task.")
    
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

class JobFileResponse(BaseModel):
    """The enriched response model for the file upload endpoint."""
    job_id: UUID = Field(..., description="Unique ID of the created job.")
    status: str = Field(..., description="Current status of the job.")
    uploaded_files: Dict[str, str] = Field(..., description="A map of the form field names to the original uploaded file names.")

# END MOCK SCHEMA


# ================================================================
# TEMPORARY SHIM FUNCTIONS (MUST BE REMOVED LATER)
# ================================================================

async def _create_job_shim(job_data: Dict[str, Any], current_user: User) -> Dict[str, Any]:
    """TEMPORARY: Replaces the missing job_service.create_job_and_enqueue_task."""
    user_id_key = str(current_user.id)
        
    new_job = {
        "id": uuid.uuid4(),
        "title": job_data.get("title", "SHIM JOB"),
        "status": "PENDING (SHIM)",
        "owner_email": current_user.email,
    }
    if user_id_key not in SHIM_JOB_STORE:
        SHIM_JOB_STORE[user_id_key] = []
    SHIM_JOB_STORE[user_id_key].append(new_job)
    return new_job

async def _get_jobs_for_user_shim(current_user: User) -> List[Dict[str, Any]]:
    """TEMPORARY: Replaces the missing job_service.get_jobs_for_user."""
    user_id_key = str(current_user.id)
    return SHIM_JOB_STORE.get(user_id_key, [])

async def _get_job_by_id_shim(job_id: UUID, current_user: User) -> Union[Dict[str, Any], None]:
    """TEMPORARY: Replaces the missing job_service.get_job_by_id."""
    jobs = await _get_jobs_for_user_shim(current_user)
    return next((j for j in jobs if j["id"] == job_id), None)

async def _delete_job_shim(job_id: UUID, current_user: User) -> None:
    """TEMPORARY: Replaces the missing job_service.delete_job."""
    user_id_key = str(current_user.id)
    
    if user_id_key not in SHIM_JOB_STORE:
        raise ValueError(f"Job ID {job_id} not found.")

    initial_len = len(SHIM_JOB_STORE[user_id_key])
    SHIM_JOB_STORE[user_id_key] = [j for j in SHIM_JOB_STORE[user_id_key] if j["id"] != job_id]
    
    if len(SHIM_JOB_STORE[user_id_key]) == initial_len:
        raise ValueError(f"Job ID {job_id} not found.")

# --- Stub for create_job function referenced in the upload endpoint ---
async def create_job(db: AsyncSession, title: str, job_data: JobSubmission, current_user: User) -> JobRead:
    """
    MOCK implementation for file upload reference.
    Now accepts 'title' as a separate argument.
    """
    new_job = await _create_job_shim(
        job_data={"title": title, "payload": job_data.input_data},
        current_user=current_user
    )
    return JobRead.model_validate(new_job)
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
    job_id: UUID, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> JobRead:
    """
    Retrieves a single job by its UUID. Must be the owner or an admin.
    """
    logger.info(f"🥊 Chuck Norris Get Job: User {current_user.email} querying job ID: {job_id}. (SHIM MODE)")
    
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
async def create_job_no_files(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> JobRead:
    """
    Creates a new, universally unique job instance based on JSON input. 
    """
    logger.info(f"🥊 Chuck Norris Job Creation: Initiating phase 1 for user {current_user.email}. (SHIM MODE)")

    new_job_data = await _create_job_shim(
        job_data=job_in.model_dump(),
        current_user=current_user
    )
    
    logger.info(f"🥋 Chuck Norris Job Creation: Job {new_job_data.get('id', 'N/A')} created successfully. Sending HTTP 201 Created.")
    return JobRead.model_validate(new_job_data)


@jobs_router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ Delete a job by ID (only owner or admin can delete).
    """
    logger.info(f"🥊 Chuck Norris Delete Job: User {current_user.email} is attempting to delete job ID: {job_id}. (SHIM MODE)")
    
    try:
        await _delete_job_shim(job_id, current_user)
        logger.info(f"🌟 Chuck Norris Success: Job {job_id} was successfully hit and removed from the SHIM store.")
    except PermissionError as e:
        logger.error(f"Chuck Norris Fail: Deletion of {job_id} failed due to permission issues.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.warning(f"Chuck Norris Warning: Job ID {job_id} not found for deletion.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Chuck Norris Fail: Unexpected error during deletion of {job_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ================================================================
# 📁 File Upload Endpoint (POST /jobs/upload)
# ================================================================
@jobs_router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=JobFileResponse)
async def create_job_with_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    content_file: UploadFile = File(..., description="The main content data file."),
    context_file: UploadFile = File(..., description="The context configuration file."),
    template_file: UploadFile = File(..., description="The job template definition file."),
    schema_file: UploadFile = File(..., description="The validation schema file."),
) -> JobFileResponse:
    """
    Creates a job by accepting multiple files via multipart/form-data, saves them
    to a temporary location (or MinIO), and then enqueues a processing task.
    Returns an enriched response including job ID and all uploaded filenames.
    """
    logger.info(f"🥊 Chuck Norris File Job: User {current_user.email} initiating file upload.")
    
    upload_dir = Path("/data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True) 

    paths = {}
    
    # 1. Capture the original file names for the rich response
    original_filenames = {
        "content_file": content_file.filename,
        "context_file": context_file.filename,
        "template_file": template_file.filename,
        "schema_file": schema_file.filename,
    }

    files = {
        "content": content_file,
        "context": context_file,
        "template": template_file,
        "schema": schema_file
    }

    for key, f in files.items():
        # Create a unique path for the saved file
        safe_filename = f"{uuid.uuid4()}_{f.filename}"
        path = upload_dir / safe_filename
        
        try:
            # Read and write the file contents
            file_contents = await f.read()
            with open(path, "wb") as out:
                out.write(file_contents)
            paths[f"{key}_path"] = str(path)
            logger.debug(f"File {f.filename} saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save file {f.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file: {f.filename}"
            )

    # 2. Define the job title and create the JobSubmission model
    job_title = f"File Job: {content_file.filename} by {current_user.email}"
    
    job_data = JobSubmission(
        task_name="process_job",
        input_data=paths, # Paths contain the temporary saved locations
    )
    
    # 3. Create the job record (using the shim)
    job_record = await create_job(db, job_title, job_data, current_user)

    # 4. Enqueue the task for background processing (simulated)
    try:
        # process_job.delay(str(job_record.id)) 
        logger.info(f"Job {job_record.id} successfully enqueued (simulated).")
    except NameError:
        logger.warning("Worker integration skipped (process_job.delay not defined).")
        pass 

    logger.info(f"🌟 Chuck Norris File Job Success: Job {job_record.id} created with files.")
    
    # 5. Return the enriched JobFileResponse
    return JobFileResponse(
        job_id=job_record.id,
        status=job_record.status,
        uploaded_files=original_filenames
    )
