# 🚀 Jobs Router - The Queue Loader
# This router is the primary interface for initiating and tracking asynchronous tasks.

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated

# --- 🛠️ Core Dependencies ---
# Assuming this is your synchronous DB session getter
from app.db.database import get_db_session_sync 
from app.core.security import get_current_user 

# --- 🥋 Service & Schema Imports ---
# JobService (The DB Muscle) and Job Task (The Celery Link)
from app.services.job_service import JobService
from app.tasks.tasks import send_processing_task 

# Job Schemas (The Data Contract)
from app.schemas.job import JobCreate, Job, JobUpdate 

logger = logging.getLogger(__name__)

# --- 🚀 Router Initialization: Starting the Brawl ---
router = APIRouter(
    prefix="/jobs",
    tags=["🎯 Job Processing: The Roundhouse Kick Router"], 
    # Use synchronous session for the API layer that interacts with the synchronous JobService
    dependencies=[Depends(get_db_session_sync), Depends(get_current_user)] 
)

# =========================================================================
# 🎯 Job Submission Endpoint: POST /jobs
# =========================================================================
@router.post(
    "/", 
    response_model=Job, 
    status_code=status.HTTP_202_ACCEPTED,
    summary="📬 Submit New Asynchronous Job",
    description="""
    Creates a new job record in the DB (PENDING) and dispatches the task to the Celery queue.
    Returns **202 Accepted** immediately.
    """
)
def create_new_job(
    job_data: JobCreate,
    db: Session = Depends(get_db_session_sync),
    # 🔐 Security check: We need the user object to assign ownership
    user: dict = Depends(get_current_user) 
):
    """
    1. Records the job in Postgres (JobService.create_job).
    2. Dispatches the heavy lifting to the Celery worker (send_processing_task.delay).
    """
    user_id = UUID(user['id'])
    
    # 1. Record the job in the database as PENDING
    try:
        db_job = JobService.create_job(db, job_data, user_id=user_id)
    except Exception as e:
        logger.error(f"Failed to record job in DB for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record job in database. Check service logs."
        )

    # 2. Dispatch the Celery task using the newly created job ID
    try:
        task = send_processing_task.delay(str(db_job.id))
        logger.info(f"Celery task sent for Job {db_job.id}. Celery ID: {task.id}")
        
        # 3. Update the job record with the Celery Task ID
        JobService.update_job(db, db_job, JobUpdate(celery_task_id=task.id))
        
    except Exception as e:
        logger.error(f"Failed to dispatch Celery task for job {db_job.id}: {e}")
        # Note: The DB still has a PENDING record. We raise an error so the user knows.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asynchronous processing service (Celery/RabbitMQ) is unavailable."
        )

    # 4. Return the database job object (which is PENDING)
    return db_job


# =========================================================================
# 🔍 Get Job Status Endpoint: GET /jobs/{job_id}
# =========================================================================
@router.get(
    "/{job_id}", 
    response_model=Job,
    summary="📊 Retrieve Job Status and Final Result",
    description="Retrieves the current status and final result URL for a specific job, enforcing user ownership."
)
def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db_session_sync),
    user: dict = Depends(get_current_user)
):
    """
    Retrieves a job by ID, enforcing that the logged-in user owns the job.
    """
    user_id = UUID(user['id'])
    db_job = JobService.get_job_by_id(db, job_id=job_id, user_id=user_id)
    
    if not db_job:
        # 404 is safer than 403 (Forbidden) as it doesn't leak whether the job ID exists
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or access denied."
        )
        
    return db_job
