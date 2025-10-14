# ============================================================
# 🧑‍💻 job_service.py — "The Job Foreman"
# ============================================================

from http.client import HTTPException
import logging
import re # 🚨 NEW: Added for basic username generation from email
import stat
from typing import List, Optional
from uuid import UUID
from datetime import datetime, UTC

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, Session

from app.db.models.job_model import Job, JobStatus
from app.db.models.user_model import User
from app.schemas.job_schema import JobSubmission # Assuming JobSubmission is here

logger = logging.getLogger(__name__)

# ============================================================
# 🗑️ DELETE JOB FUNCTION
# ============================================================

async def delete_job(db: AsyncSession, job_id: UUID, user_id: UUID) -> None:
    """
    Deletes a Job record from the database if it belongs to the specified user.

    Args:
        db (AsyncSession): The database session.
        job_id (UUID): The ID of the job to delete.
        user_id (UUID): The ID of the user attempting to delete the job.

    Raises:
        HTTPException: If the job does not exist or does not belong to the user.
    """
    # 1. Retrieve the job to ensure it exists and belongs to the user
    job = await get_job_by_id(db, job_id, user_id)
    if job is None:
        logger.warning(f"Job {job_id} not found for user {user_id}.")
        raise HTTPException(status_code=stat.HTTP_404_NOT_FOUND, detail="Job not found.")

    # 2. Delete the job
    await db.delete(job)
    await db.commit()
    logger.info(f"Job {job_id} deleted successfully for user {user_id}.")
    
# ============================================================
# 🎯 JOB CREATION & ASYNC UPDATE (FOR API ROUTERS)
# ============================================================
async def create_job(
    db: AsyncSession, job_data: JobSubmission, user: User
) -> Job:
    """
    Creates a new Job record in the database with PENDING status.

    ⭐️ FIX: We correctly map 'task_name' (from the Pydantic schema) to
    'celery_task_name' (in the SQLAlchemy model) to satisfy the NOT NULL constraint.
    """
    # 1. Extract the task_name for the specific column
    task_name_value = job_data.task_name

    # 2. Dump the data, explicitly excluding the 'task_name' field from the generic dump
    # so we can pass it separately with the correct column name.
    job_data_dict = job_data.model_dump(exclude={"task_name"})

    # 3. Instantiate the Job model with the explicit celery_task_name
    new_job = Job(
        **job_data_dict,
        user_id=user.id,
        status=JobStatus.PENDING,
        # ⭐️ FIX IMPLEMENTED HERE ⭐️
        celery_task_name=task_name_value,
    )

    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    logger.info(
        f"Job {new_job.job_id} created in DB for user {user.id}."
    )
    return new_job


async def update_job_id(
    db: AsyncSession, db_job: Job, celery_task_id: str
) -> None:
    """Updates a Job record with the Celery task ID post-dispatch."""
    db_job.celery_task_id = celery_task_id
    await db.commit()
    logger.info(
        f"Job {db_job.job_id} updated with Celery ID: {celery_task_id}"
    )


# ============================================================
# ⚙️ SYNCHRONOUS CELERY UPDATE (FOR WORKER CONTEXT)
# ============================================================
def update_job_status_for_celery(
    db: Session, job_id: UUID, update_data: dict
) -> None:
    """
    Synchronous update function dedicated for Celery workers.
    """
    try:
        # Map string status from worker (PROCESSING/COMPLETED) to Enum
        if 'status' in update_data:
            status_str = update_data['status']
            if status_str == "PROCESSING":
                update_data['status'] = JobStatus.RUNNING
            elif status_str == "COMPLETED":
                update_data['status'] = JobStatus.SUCCESS
            else:
                # Handles PENDING, FAILURE, TERMINATED if sent as string
                update_data['status'] = JobStatus(status_str)

        # Use a synchronous update query
        stmt = (
            update(Job)
            .where(Job.job_id == job_id)
            .values(
                **update_data,
                updated_at=datetime.now(UTC)
            )
        )

        db.execute(stmt)
        db.commit()
        logger.debug(
            f"Job {job_id} sync status updated to {update_data.get('status', 'N/A')}."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to perform sync status update for job {job_id}: {e}")
        raise


# ============================================================
# 🔍 SINGLE JOB RETRIEVAL (SECURELY)
# ============================================================
async def get_job_by_id(
    db: AsyncSession, job_id: UUID, user_id: UUID
) -> Optional[Job]:
    """Retrieves a Job by its ID, ENSURING it belongs to the specified user."""
    stmt = (
        select(Job)
        .where(
            Job.job_id == job_id,
            Job.user_id == user_id,
        )
        .options(selectinload(Job.user))
    )

    result = await db.execute(stmt)
    db_job = result.scalar_one_or_none()

    return db_job


# ============================================================
# 📜 MULTIPLE JOB RETRIEVAL (FOR LISTING/FILTERING)
# ============================================================

async def _get_jobs_filtered(
    db: AsyncSession, user_id: UUID, statuses: Optional[List[JobStatus]] = None
) -> List[Job]:
    """Internal helper to retrieve jobs for a user, optionally filtered by status."""
    stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())

    if statuses:
        stmt = stmt.where(Job.status.in_(statuses))

    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def get_jobs_for_user(db: AsyncSession, user_id: UUID) -> List[Job]:
    """Retrieves all jobs for a specific user."""
    return await _get_jobs_filtered(db, user_id)


async def get_active_jobs_for_user(db: AsyncSession, user_id: UUID) -> List[Job]:
    """Retrieves jobs that are PENDING or RUNNING."""
    active_statuses = [JobStatus.PENDING, JobStatus.RUNNING]
    return await _get_jobs_filtered(db, user_id, active_statuses)


async def get_failed_jobs_for_user(db: AsyncSession, user_id: UUID) -> List[Job]:
    """Retrieves jobs that have FAILED."""
    return await _get_jobs_filtered(db, user_id, [JobStatus.FAILURE])


async def get_finished_jobs_for_user(db: AsyncSession, user_id: UUID) -> List[Job]:
    """Retrieves jobs that are SUCCESS or TERMINATED."""
    finished_statuses = [JobStatus.SUCCESS, JobStatus.TERMINATED]
    return await _get_jobs_filtered(db, user_id, finished_statuses)

# ============================================================
# 🔨 User Utility for Router (Used to create username for DB)
# ============================================================
def generate_username_from_email(email: str) -> str:
    """Generates a simple username from the local part of an email."""
    if not email:
        return ""
    # Get the part before the @
    username_part = email.split('@')[0]
    # Simple sanitization: remove non-alphanumeric characters (except - and _)
    return re.sub(r'[^\w-]', '', username_part).lower()
