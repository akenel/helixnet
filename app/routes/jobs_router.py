# /code/app/routes/jobs_router.py

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# --- ⚙️ Core Dependencies & Database ---
from app.db.database import get_db_session 
from app.core.security import get_current_user 

# --- 📦 Models and Schemas ---
from app.db.models.user import User # Type hint for ORM model (optional, but clean)
from app.schemas.jobs import JobSubmission, JobStatus # JobStatus is used for the response
from app.schemas.user import UserInDB # For dependency type hint
from app.services.job_service import submit_job, get_job_by_id
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Any

# --- 🛣️ Router Initialization ---
jobs_router = APIRouter(
    tags=["🎯  Job Processing : jobs_router"], # This tag appears in Swagger
    dependencies=[Depends(get_current_user)] # All job routes require auth
)

# Example response object for Swagger documentation
JOB_SUBMISSION_EXAMPLE = {
    "job_id": "c64b9721-7c4a-4ca8-bdc4-2a9b1a85530a",
    "status": "PENDING",
    "message": "🌼️ Job successfully submitted and queued for processing.",
    "result_data": None
}
# --------------------------------------------------------------------------
# 🎯 Job Submission Endpoint: submit_process_job
# --------------------------------------------------------------------------
@jobs_router.post(
    "/",
    response_model=JobStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="📬 Submit New Asynchronous Job", # Concise summary with emoji
    description="""
    Submits a complex data processing job to the background worker (Celery).
    
    1. **DB Record:** A job tracking record is immediately persisted to PostgreSQL.
    2. **Queue:** The actual heavy lifting is offloaded to the RabbitMQ queue.
    
    Returns **202 Accepted** (not 200 OK) because processing is asynchronous.
    """,
    response_description="Returns the initial job status and ID for tracking.",
    responses={
        202: {
            "model": JobStatus,
            "description": "Job accepted and queued.",
            "content": {
                "application/json": {
                    "example": JOB_SUBMISSION_EXAMPLE
                }
            }
        }
    }
)
async def submit_process_job(
    job_data: JobSubmission,
    current_user: Annotated[UserInDB, Depends(get_current_user)], 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submits the primary data processing job by delegating to the service layer.
    The service layer handles: 1) DB record creation, and 2) Celery task queuing.
    """
    
    # KIS Solution: Call the unified service function
    result = await submit_job(
        db=db,
        input_data=job_data, 
        user_id=current_user.id 
    )
    
    return result

# --------------------------------------------------------------------------
# 🔍 Get Job Status Endpoint
# --------------------------------------------------------------------------
@jobs_router.get(
    "/{job_id}",
    response_model=JobStatus,
    summary="📊 Retrieve Job Status and Final Result", # Concise summary with emoji
    description="""
    Retrieves the persistent job status and final result data from the PostgreSQL database.
    
    * **PENDING/STARTED:** The job is queued or actively running.
    * **SUCCESS:** The job completed. `result_data` will contain the final JSON output.
    * **FAILURE:** The job failed. `message` will contain the error details.
    """,
    response_description="Returns the current status object, including final results upon success.",
)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve the status and results of a specific job."""
    
    job = await get_job_by_id(db, job_id)
    
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or not authorized.")
        
    return job 