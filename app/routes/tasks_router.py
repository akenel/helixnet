"""
API Endpoints for submitting and monitoring Celery background tasks.
"""
from fastapi import APIRouter, status, Depends, HTTPException
from typing import Dict
from uuid import UUID

# CRITICAL FIX: Use async session from SQLAlchemy extension
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # For SQLAlchemy 2.0 async querying

from app.tasks.celery_app import celery_app
from app.tasks.tasks import process_job

# CRITICAL FIX: Import the actual function name exported by database.py
from app.db.database import get_db_session 
# /home/angel/repos/helixnet/app/models/task_model.py
from app.models.task_model import TaskResult
from app.db.models.job_result import JobResult

from app.tasks.tasks import sanity_check_task

from app.schemas.tasks import JobSubmission

# The object that is imported by main.py
tasks_router = APIRouter()

# --- Utility Function (MUST BE ASYNC) ---
async def get_job_result_from_db(session: AsyncSession, task_id: str) -> JobResult:
    """
    Helper to retrieve job result from the database asynchronously.
    Uses SQLAlchemy 2.0 style select and execute.
    """
    # Use SQLAlchemy 2.0 style to build the async query
    stmt = select(JobResult).filter(JobResult.task_id == task_id)
    # Execute the query asynchronously
    result = await session.execute(stmt)
    # Extract the first scalar result (the JobResult object)
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job result not found in database.")
    return job


# --- 1. Sanity Check ---
@tasks_router.get(
    "/sanity-check", 
    status_code=status.HTTP_202_ACCEPTED, 
    response_model=Dict[str, str]
)
def trigger_sanity_check():
    """Submits a quick task to the worker to ensure Celery is responsive."""
    result = sanity_check_task.delay()
    return {"task_id": result.id, "status": "Task queued successfully."}


# --- 2. Submit Main Job (Triggers DB Insert) ---
@tasks_router.post(
    "/process", 
    status_code=status.HTTP_202_ACCEPTED, 
    response_model=Dict[str, str]
)
def submit_process_job(job_data: JobSubmission):
    """
    Submits the primary data processing job. 
    The worker will handle creating the PENDING record in Postgres upon startup.
    """
    # The 'process_job' task requires the user_id and input data
    result = process_job.delay(str(job_data.user_id), job_data.input_data)
    
    return {
        "task_id": result.id, 
        "status": "Processing job queued and database record initialized (PENDING)."
    }


# --- 3. Check Volatile Status (Celery Backend/Redis) ---
@tasks_router.get(
    "/status/{task_id}", 
    response_model=Dict[str, str], 
    tags=["Tasks - Volatile"]
)
def get_task_status_volatile(task_id: str):
    """
    Checks the task status using the Celery result backend (Redis). 
    Status is volatile and may be lost on restart.
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'FAILURE':
        response = {
            "task_id": task_id,
            "status": task.state,
            "error": str(task.result)
        }
    else:
        response = {
            "task_id": task_id,
            "status": task.state,
            "result_summary": "Check /tasks/persistent-status/{task_id} for final data."
        }
        
    return response


# --- 4. Check Persistent Status (PostgreSQL) ---
@tasks_router.get(
    "/persistent-status/{task_id}", 
    response_model=Dict, 
    tags=["Tasks - Persistent"]
)
# CRITICAL FIX: Function must be async, use the correct dependency name and AsyncSession type
async def get_task_status_persistent(
    task_id: UUID, 
    session: AsyncSession = Depends(get_db_session)
):
    """
    Checks the persistent job result and status from the PostgreSQL database.
    This provides the final, non-volatile result.
    """
    # CRITICAL FIX: Await the async helper function
    job = await get_job_result_from_db(session, str(task_id))
    
    return {
        "task_id": str(job.task_id),
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "result_data": job.result_data
    }
