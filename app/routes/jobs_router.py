import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

# --- 🛠️ Dependencies: The Unstoppable Force ---
from app.db.database import get_db_session 
from app.core.security import get_current_user 

# --- 🥋 Data Schemas & Models ---
# The User model is here, because even Chuck needs to know who he's fighting for.
from app.db.models.user import User 
from app.schemas.jobs import JobSubmission, JobStatus 
from app.schemas.user import UserInDB 
from app.services.job_service import submit_job, get_job_by_id

# --- 🚀 Router Initialization: Starting the Brawl ---
jobs_router = APIRouter(
    tags=["🎯 Job Processing: The Roundhouse Kick Router"], # Swagger knows what's up.
    dependencies=[Depends(get_current_user)] # No access unless authenticated. Chuck said so.
)

# Example: The kind of status that comes back when Chuck is involved.
JOB_SUBMISSION_EXAMPLE = {
    "job_id": "c64b9721-7c4a-4ca8-bdc4-2a9b1a85530a",
    "status": "PENDING",
    "message": "🔥 Job successfully submitted. It knows better than to be slow.",
    "result_data": None
}

# =========================================================================
# 🎯 Job Submission Endpoint: The Submission Dominator
# =========================================================================
@jobs_router.post(
    "/submit",
    response_model=JobStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="📬 Submit New Asynchronous Job",
    description="""
    This endpoint doesn't wait. It takes the job data and **sends it to Celery**.
    
    * **DB Record:** Persisted immediately.
    * **Queue:** Offloaded to the RabbitMQ queue.
    
    We return **202 Accepted** because the job is now Celery's problem.
    """,
    responses={
        202: {
            "model": JobStatus,
            "description": "Job accepted and queued. It will be dealt with.",
            "content": {"application/json": {"example": JOB_SUBMISSION_EXAMPLE}}
        }
    }
)
async def submit_process_job(
    # The JSON data body. It must be present, or Chuck will be unhappy.
    job_data: JobSubmission, 
    # This is the authenticated user from the Bearer Token. They paid the price of admission.
    current_user: Annotated[UserInDB, Depends(get_current_user)], 
    # The database session. It handles the persistence.
    db: AsyncSession = Depends(get_db_session)
):
    """
    Kicks the job submission into the service layer.
    """
    
    # One line, one execution. That's the way Chuck likes it.
    job_submission_result = await submit_job(
        db=db,
        input_data=job_data, 
        user_id=current_user.id 
    )
    
    return job_submission_result

# =========================================================================
# 🔍 Get Job Status Endpoint: The Accountability Check
# =========================================================================
@jobs_router.get(
    "/{job_id}",
    response_model=JobStatus,
    summary="📊 Retrieve Job Status and Final Result",
    description="""
    Checks the status of a job. If the job belongs to someone else, you get nothing. 
    
    * **PENDING/STARTED:** Still running.
    * **SUCCESS:** The final result is ready. 💥
    * **FAILURE:** Something broke. Chuck will investigate.
    """,
    response_description="Returns the status object."
)
async def get_job_status(
    # The ID of the job to retrieve. UUID, not some weak integer.
    job_id: uuid.UUID,
    # Still need the user to verify ownership. Security first.
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve the status and results of a specific job."""
    
    job = await get_job_by_id(db, job_id)
    
    # Unauthorized access? That's a 404. Chuck is not amused.
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or not authorized. Don't touch what isn't yours.")
        
    return job
