# app/services/job_service.py — 🥋 The Job Master Service
# ====================================================================================

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

# --- Core SQLAlchemy & ASYNC Imports ---
# 🚨 CN QA: Eliminated redundant Session imports and consolidated to AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, UUID
from sqlalchemy.orm import Session # Keep only if needed for sync functions (Celery)
from sqlalchemy.future import select # Best practice for select statement in async

# --- Model & Schema Imports ---
from app.db.models.job_model import Job
from app.db.models.user_model import User
# 🚨 CN QA: Using concrete names for clarity instead of ambiguous aliases (JobStatus, JobUpdate)
from app.db.models.job_model import Job as JobModel 

from app.db.models.job_model import Job as JobORM 

from app.schemas.job_schema import (
    JobSubmission, 
    JobUpdate  # ⬅️ This is the correct schema name for status/result updates
)

logger = logging.getLogger(__name__)

# ============================================================
# 🎯 ASYNCHRONOUS FUNCTIONS (FastAPI & Internal Async Use)
# ============================================================

async def create_job(db: AsyncSession, job_data: JobSubmission, user: User) -> Job:
    """
    1️⃣ Creates a new Job record in the database.
    2️⃣ Manages the complex extraction of nested fields required by the ORM.
    """
    logger.info(f"Preparing job record for user {user.id}.")

    # 1. Prepare data and isolate the core payload
    job_data_dict = job_data.model_dump(exclude_none=True)
    task_name_value = job_data_dict.pop('task_name', None) 
    
    # The 'input_data' field holds the entire JSON payload submitted by the user.
    # We treat it as the payload dictionary.
    input_payload = job_data_dict.get('input_data', {})

    # 2. 💥 CN FIX: Extract 'name' from the NESTED input_payload 
    #    This prevents the IntegrityError and sets the ORM name column correctly.
    job_name = input_payload.pop('name', None) 
    
    # Update the job_data_dict with the cleaned input_payload (without 'name')
    job_data_dict['input_data'] = input_payload
    
    # 3. Instantiate the Job ORM object
    db_job = Job(
        **job_data_dict, 
        celery_task_name=task_name_value,
        user_id=user.id,
        name=job_name, # 👈 Assigned to the top-level 'name' column
    )
    
    # 4. Add to DB, commit, and refresh (MUST use await with AsyncSession)
    db.add(db_job)
    await db.commit() # 👈 No commit, no glory.
    await db.refresh(db_job) # 👈 Refresh to populate default fields (like job_id)

    logger.info(f"Job {db_job.job_id} created successfully.")
    return db_job


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Job]:
    """Retrieve a job by ID, scoped to the user for security."""

    # 💡 ASYNC pattern: execute(select(...))
    stmt = select(Job).where(Job.id == job_id, Job.user_id == user_id)
    result = await db.execute(stmt)
    
    # Use scalar_one_or_none() for single object retrieval
    job = result.scalar_one_or_none() 

    return job

async def get_jobs_for_user(db: AsyncSession, user_id: uuid.UUID) -> List[Job]:
    """Retrieves all jobs for a specific user."""

    # 💡 ASYNC pattern: execute(select(...)).scalars().all()
    stmt = (
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
    )
    result = await db.execute(stmt)
    # Use .scalars().all() to get a list of ORM objects directly
    jobs = result.scalars().all() 

    return jobs

async def update_job_id(db: AsyncSession, db_job: Job, celery_task_id: str) -> None:
    """Updates the Celery task ID on an existing Job ORM object and commits."""
    
    # The 'db_job' object is already attached to the session (from create_job refresh)
    db_job.celery_task_id = celery_task_id
    
    # Commit the update
    await db.commit()
    await db.refresh(db_job)

async def update_job_status(
    db: AsyncSession, job_id: uuid.UUID, status_update: JobUpdate
) -> Optional[Job]:
    """
    Updates the status and result data of a job (Used by FastAPI/other async internal calls).
    """
    # 1. Retrieve the job (Async)
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        logger.warning(f"❌ Job ID {job_id} not found for status update (Async).")
        return None

    # 2. Update fields on the ORM object
    job.status = status_update.status

    if status_update.result_data is not None:
        job.result_data = status_update.result_data

    # The updated_at column should handle itself, but we manually set finished_at
    if status_update.status in ["SUCCESS", "FAILED"]:
        job.finished_at = datetime.now(UTC)

    if status_update.task_id:
        job.celery_task_id = str(status_update.task_id)

    # 3. Commit the changes (Async)
    await db.commit()
    await db.refresh(job)
    logger.info(f"✅ Job {job_id} status updated to: {job.status} (Async)")
    return job


# ============================================================
# 🚧 SYNCHRONOUS FUNCTIONS (Primarily for Celery Task Use)
# ============================================================

# 🚨 CN QA: We rename 'update_job_status_sync' to clarify its use for Celery.
# 🚨 CRITICAL FIX: The function must be a standard 'def' as it's called synchronously by Celery.

def update_job_status_for_celery(
    db: Session, job_id: uuid.UUID, status_update: dict
) -> Optional[Job]:
    """
    Updates job status/result. MUST use a synchronous Session for Celery/workers.
    """
    # 1. Retrieve the job using synchronous SQLAlchemy ORM query
    job = db.query(JobORM).filter(JobORM.job_id == job_id).first()
    if not job:
        logger.warning(f"❌ Job ID {job_id} not found for status update (Sync Celery).")
        return None
    
    # 2. Update fields using the dictionary passed from the worker
    if 'status' in status_update:
        job.status = status_update['status']

    if 'result_data' in status_update and status_update['result_data'] is not None:
        job.result_data = status_update['result_data']

    if job.status in ["SUCCESS", "FAILED"]:
        job.finished_at = datetime.now(UTC)

    if 'task_id' in status_update:
        job.celery_task_id = status_update['task_id']

    # 3. Commit the changes (synchronous)
    db.commit() # 👈 No 'await' for sync Session
    db.refresh(job)
    logger.info(f"✅ Job {job_id} status updated to: {job.status} (Sync Celery)")
    return job

# 🚨 CN QA: 'queue_job_task' is a mock and can remain simple.
def queue_job_task(
    job_id: uuid.UUID, submission_data: JobSubmission, user_id: uuid.UUID
) -> bool:
    """
    Mocks queuing a job. In a real application, this is internal Celery logic.
    """
    logger.info(
        f"MOCK: Queuing job {job_id} for user {user_id} with data: {submission_data.input_data}"
    )
    return True