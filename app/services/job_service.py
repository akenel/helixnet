# app/services/job_service.py
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
# ASYNC imports for FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID, select 
# SYNC import for Celery
from sqlalchemy.orm import Session
from app.db.models.job_result import JobResult
from app.schemas.job import JobSubmission, JobStatus

import logging
from uuid import UUID
from sqlalchemy.orm import Session

# Import the model and schemas
from app.db.models.job import JobModel
from app.schemas.job import JobCreate, JobUpdate, JobStatus

logger = logging.getLogger(__name__)
# --- Synchronous Functions (Celery/External Use) ---

def queue_job_task(job_id: uuid.UUID, submission_data: JobSubmission, user_id: uuid.UUID) -> bool:
    """
    Mocks queuing a job. 
    In a real application, this would dispatch the job to a Celery/Redis worker.
    This remains a standard 'def' function.
    """
    print(f"MOCK: Queuing job {job_id} for user {user_id} with data: {submission_data.input_data}")
    return True

def update_job_status_sync(db: Session, job_id: uuid.UUID, status_update: JobStatus) -> Optional[JobResult]:
    """
    Updates the status and result data of a job. 
    ***Used by synchronous Celery tasks.***
    """
    # 1. Retrieve the job using synchronous SQLAlchemy ORM query
    # NOTE: No 'await', uses synchronous Session methods.
    job = db.query(JobResult).filter(JobResult.id == job_id).first()
  
    if not job:
        print(f"❌ WARNING: Job ID {job_id} not found for status update (Sync).")
        return None

    # 2. Update fields on the ORM object (same logic as async version)
    job.status = status_update.status
    
    if status_update.result_data is not None:
        job.result_data = status_update.result_data
    
    if status_update.status in ["SUCCESS", "FAILED"]:
        job.finished_at = datetime.now(UTC)
    
    if status_update.task_id:
        job.task_id = str(status_update.task_id) 

    # 3. Commit the changes (synchronous)
    db.commit()
    db.refresh(job)
    print(f"✅ Job {job_id} status updated to: {job.status} (Sync)")
    return job

# --- Asynchronous Functions (FastAPI Use) ---
# ... update_job_status function (this is imported by the task) ...
async def create_new_job(
        # 💡 FIX: Use the correct Pydantic model name from your code: JobSubmission
        # We also simplify the parameters to what is actually needed for object creation
        db: AsyncSession, 
        user_id: uuid.UUID,
        submission_data: JobSubmission, # <-- Correct name for the Pydantic input!
        task_name: str
) -> JobResult:

    """Creates a new JobResult entry with status=PENDING. Used by FastAPI."""
    
    new_job = JobResult(
        user_id=user_id,
        # 💡 FIX: Access the input data from the correct Pydantic field
        job_input=submission_data.input_data, 
        task_name=task_name,
        status="PENDING",
        created_at=datetime.now(UTC)
    )

# 1. Add the job to the session
    db.add(new_job)

# 2. 💡 CRITICAL FIX: Deferred import using the Standard Task Name
    from app.tasks.tasks import process_job 
 
# 3. CRITICAL: Send the Celery task and capture the result object
# Note: Celery tasks only accept data types that can be serialized (str, dict, list, etc.), 
# so we pass str(new_job.id) and the dict/data fields.
    task_result = process_job.delay(
        job_id=str(new_job.id), 
        user_id=str(user_id), 
        input_data=submission_data.input_data
    ) 

# 4. CRITICAL FIX: Update the job model with the task ID *before* commit
    new_job.task_id = task_result.id 
    
# 5. Commit the full model, including the newly set task_id
    await db.commit() 
    await db.refresh(new_job)
    return new_job
# --- Now we fix submit_job to call the fixed create_new_job ---
# In /code/app/services/job_service.py

async def submit_job(db: AsyncSession, input_data: JobSubmission, user_id: uuid.UUID) -> Dict[str, Any]:
    """Handles the entire job submission process. Used by FastAPI."""
    
    # --- 1. Create the initial DB record ---
    # This must happen first to get the job_id
    new_job_record = await create_new_job(
        db=db, 
        user_id=user_id, 
        submission_data=input_data, 
        task_name="app.tasks.process_job" 
    )
    
    # This prevents the module from trying to import the task at startup.
    from app.tasks.tasks import process_job 
    
    # --- 2. Enqueue the task with ALL REQUIRED PARAMETERS (The Fix!) ---
    # Convert Pydantic model to dictionary for Celery serialization
    # Convert UUIDs to strings for Celery serialization
    celery_result = process_job.delay(
        str(new_job_record.id),              # required positional argument 1 (job_id)
        str(user_id),                        # required positional argument 2 (user_id)
        input_data.model_dump()              # required positional argument 3 (input_data as dict)
    ) 
    
    # NOTE: You should ideally save the celery_result.id (the task ID) to the new_job_record here.
    
    # 3. Return the result
    return {
        "message": "🌼️ Job successfully submitted and queued.",
        "job_id": str(new_job_record.id),
        "status": new_job_record.status,
    }


async def get_job_by_id(db: AsyncSession, job_id: uuid.UUID) -> Optional[JobStatus]:
    """Retrieve a job from the database by ID. Used by FastAPI."""
    
    # 💡 ASYNC pattern: await db.execute(select(...))
    stmt = select(JobResult).where(JobResult.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        return None

    return JobStatus.model_validate(job)

async def get_jobs_for_user(db: AsyncSession, user_id: uuid.UUID) -> List[JobStatus]:
    """Retrieves all jobs for a specific user. Used by FastAPI."""
    
    # 💡 ASYNC pattern: await db.execute(select(...)).scalars().all()
    stmt = select(JobResult).where(JobResult.user_id == user_id).order_by(JobResult.created_at.desc())
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    return [JobStatus.model_validate(job) for job in jobs]

async def update_job_status(db: AsyncSession, job_id: uuid.UUID, status_update: JobStatus) -> Optional[JobResult]:
    """
    Updates the status and result data of a job. 
    ***Used by FastAPI/other async internal calls.***
    """
    # 1. Retrieve the job (Async)
    stmt = select(JobResult).where(JobResult.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
  
    if not job:
        print(f"❌ WARNING: Job ID {job_id} not found for status update (Async).")
        return None

    # 2. Update fields on the ORM object (same logic)
    job.status = status_update.status
    
    if status_update.result_data is not None:
        job.result_data = status_update.result_data
    
    if status_update.status in ["SUCCESS", "FAILED"]:
        job.finished_at = datetime.now(UTC)
    
    if status_update.task_id:
        job.task_id = str(status_update.task_id) 

    # 3. Commit the changes (Async)
    await db.commit()
    await db.refresh(job)
    print(f"✅ Job {job_id} status updated to: {job.status} (Async)")
    return job


# 🛡️ Job Service - The Async Ledger Controller
# This service handles all database interactions for the Job model.


class JobService:
    """
    Central service layer for managing Job entities in the database.
    Abstracts all SQLAlchemy interactions, ensuring data integrity.
    """
    model = JobModel # Reference to the SQLAlchemy model

    @staticmethod
    def create_job(db: Session, job_data: JobCreate, user_id: UUID) -> JobModel:
        """
        Records a new PENDING job in the database immediately after a user request.
        The Celery task will reference this entry.
        """
        logger.info(f"Creating new job for user {user_id}.")
        
        db_job = JobModel(
            user_id=user_id,
            input_file_path=job_data.input_file_path,
            template_name=job_data.template_name,
            initial_config=job_data.initial_config,
            # Start job in PENDING state
            status=JobStatus.PENDING 
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Job {db_job.id} created and set to PENDING.")
        return db_job

    @staticmethod
    def get_job_by_id(db: Session, job_id: UUID, user_id: UUID = None) -> Optional[JobModel]:
        """
        Fetches a job by ID. If user_id is provided, enforces ownership check.
        """
        query = db.query(JobModel).filter(JobModel.id == job_id)
        
        # Enforce security: only allow the owner (or an admin/internal process) to view the job
        if user_id:
            query = query.filter(JobModel.user_id == user_id)
            
        return query.first()

    @staticmethod
    def update_job(db: Session, db_job: JobModel, update_data: JobUpdate) -> JobModel:
        """
        Updates the job record, typically called by the Celery worker to change status.
        """
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(db_job, key, value)
            
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Job {db_job.id} updated. New status: {db_job.status.value}")
        return db_job
    
    @staticmethod
    def get_jobs_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> list[JobModel]:
        """
        Retrieves all jobs submitted by a specific user (for the /jobs endpoint).
        """
        return db.query(JobModel).filter(JobModel.user_id == user_id).offset(skip).limit(limit).all()
