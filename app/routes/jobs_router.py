# 🧭 jobs_router.py — "The Queue Commander" (CN PERFECTO VERSION)
# ============================================================

import logging
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession # 🎯 Use AsyncSession everywhere!

# 🧱 --- Core System Imports ---
from app.db.database import get_db_session # 🎯 Using the ASYNC session generator
from app.db.models.user_model import User
from app.db.models.job_model import Job
from app.schemas.job_schema import JobSubmission, JobRead
from app.services import job_service
from app.services.user_service import get_current_user
from app.tasks.job_tasks import process_data 
# 🎛️ --- Initialize Logger & Router ---
logger = logging.getLogger(__name__)
jobs_router = APIRouter()


# ============================================================
# 🎯 CREATE NEW JOB (POST /jobs)
# ============================================================
@jobs_router.post(
    "/",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="📬 Submit a new asynchronous job",
    description="""
    1️⃣ Creates a new job record in Postgres with status **PENDING** 2️⃣ Dispatches the task to the Celery queue
    3️⃣ Returns the created job immediately (HTTP 202)
    """,
)
async def create_job( # 🎯 ROUTER MUST BE ASYNC
    job_data: JobSubmission,
    db: AsyncSession = Depends(get_db_session), # 🎯 ASYNC SESSION
    current_user: User = Depends(get_current_user),
) -> Job:
    """
    🧩 Steps:
    1. Insert the new Job record into Postgres (status=PENDING)
    2. Push an async task to Celery for background processing
    3. Return the Job to the user immediately
    """

    user_id = current_user.id
    logger.info(f"📦 User {user_id} submitting new job...")

    # Step 1️⃣ — Record job in DB
    try:
        # 🎯 MUST AWAIT THE SERVICE CALL
        db_job = await job_service.create_job(db=db, job_data=job_data, user=current_user)
        logger.info(
            f"🪣 Job {db_job.job_id} recorded in DB with status {db_job.status}"
        )
    except Exception as e:
        logger.error(f"💥 Failed to record job in DB for user {user_id}: {e}")
        # The service layer should ideally handle its own transaction rollback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record job in database. Please retry later.",
        )

    # Step 2️⃣ & 3️⃣ — Send Celery Task and Update ID
    try:
        task = process_data.delay(str(db_job.job_id))

        # 🎯 CN FIX: Use a clean, awaited update function call
        await job_service.update_job_id(
            db=db,
            db_job=db_job, # Pass the ORM object
            celery_task_id=task.id, # Pass the ID directly
        )

        logger.info(
            f"🚀 Celery task dispatched for Job {db_job.job_id}. Task ID: {task.id}"
        )

    except Exception as e:
        logger.error(f"⚠️ Failed to dispatch Celery task for job {db_job.job_id}: {e}")
        # Only raise 503 if the Celery system is essential and down
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asynchronous processing unavailable. Job left in PENDING.",
        )

    logger.info(f"✅ Job {db_job.job_id} accepted for background processing.")
    return db_job


# ============================================================
# 🔍 GET JOB STATUS (GET /jobs/{job_id})
# ============================================================
@jobs_router.get(
    "/{job_id}",
    response_model=JobRead,
    summary="📊 Retrieve Job Status",
    description="Fetches the job’s current status and result (if available).",
)
async def get_job_status( # 🎯 MUST BE ASYNC
    job_id: UUID,
    db: AsyncSession = Depends(get_db_session), # 🎯 ASYNC SESSION
    current_user: User = Depends(get_current_user), # User object, not dict
) -> Job:
    """
    🧩 Steps:
    1. Retrieve a specific Job by ID
    2. Ensure the requesting user owns that job
    3. Return the job record and its status/result
    """

    user_id = current_user.id
    logger.info(f"🔍 Checking job {job_id} for user {user_id}")

    # 🎯 MUST AWAIT THE SERVICE CALL
    db_job = await job_service.get_job_by_id(db=db, job_id=job_id, user_id=user_id)

    if not db_job:
        logger.warning(f"🚫 Job {job_id} not found or access denied for {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or access denied.",
        )

    logger.info(f"📈 Job {job_id} retrieved successfully (status={db_job.status})")
    return db_job


# ============================================================
# 🧹 BONUS: GET ALL JOBS FOR USER (GET /jobs)
# ============================================================
@jobs_router.get(
    "/",
    response_model=List[JobRead],
    summary="📜 List All Jobs for Current User",
)
async def list_user_jobs( # 🎯 MUST BE ASYNC
    db: AsyncSession = Depends(get_db_session), # 🎯 ASYNC SESSION
    current_user: User = Depends(get_current_user), # User object, not dict
) -> List[Job]:
    """Returns all jobs belonging to the logged-in user."""
    user_id = current_user.id
    logger.info(f"🧾 Listing all jobs for user {user_id}")

    # 🎯 MUST AWAIT THE SERVICE CALL
    jobs = await job_service.get_jobs_for_user(db=db, user_id=user_id)
    return jobs