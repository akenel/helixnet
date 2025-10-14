"""
API Endpoints for monitoring Celery background tasks.
Job submission logic has been moved to app/routes/jobs_router.py.
"""
from fastapi import APIRouter, status, Depends, HTTPException
from typing import Dict
from uuid import UUID  # Use UUID alias for clarity

# --- SQLAlchemy and DB Dependencies ---
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db_session

# --- Models and Schemas ---
from app.db.models.task_model import TaskStatus
from app.db.models.task_model import TaskResult # Correct model for persistent result

# --- Celery and Task Dependencies ---
from app.db.models.job_model import JobStatus
from app.tasks.celery_app import celery_app

# Import the necessary DB utility, Service, and Schemas
from app.tasks.db_utils import get_db_worker

# The object that is imported by main.py
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])


# --------------------------------------------------------------------------
# --- Utility Function (FIXED: Uses TaskResult) ---
# --------------------------------------------------------------------------
async def get_job_result_from_db(session: AsyncSession, task_id: str) -> TaskResult:
    """
    Helper to retrieve job result from the database asynchronously.
    """
    # Use SQLAlchemy 2.0 style to build the async query
    # FIX: Use TaskResult model for the query
    stmt = select(TaskResult).filter(TaskResult.task_id == task_id)
    # Execute the query asynchronously
    result = await session.execute(stmt)
    # Extract the first scalar result (the TaskResult object)
    job = result.scalars().first()

    if not job:
        # Use HTTP 404 for not found (standard REST practice)
        raise HTTPException(
            status_code=404, detail=f"Task result not found for ID: {task_id}"
        )
    return job


# --------------------------------------------------------------------------
# --- 1. Sanity Check (Stays) ---
# --------------------------------------------------------------------------


@tasks_router.get(
    "/sanity-check", status_code=status.HTTP_202_ACCEPTED, response_model=Dict[str, str]
)
def trigger_sanity_check():
    """Submits a quick task to the worker to ensure Celery is responsive."""
    result = get_db_worker.delay()
    return {"task_id": result.id, "status": "Task queued successfully."}


# --------------------------------------------------------------------------
# --- 3. Check Volatile Status (Celery Backend/Redis) ---
# --------------------------------------------------------------------------
@tasks_router.get(
    "/status/{task_id}", response_model=JobStatus, tags=["Tasks - Volatile"]
)
def get_task_status_volatile(task_id: str):
    """
    Checks the task status using the Celery result backend (Redis).
    Status is volatile and may be lost on restart.
    """
    task = celery_app.AsyncResult(task_id)

    if task.state == "FAILURE":
        response = {"task_id": task_id, "status": task.state, "error": str(task.result)}
    else:
        response = {
            "task_id": task_id,
            "status": task.state,
            "result_summary": "Check /tasks/persistent-status/{task_id} for final data.",
        }

    return response


# --------------------------------------------------------------------------
# --- 4. Check Persistent Status (PostgreSQL) ---
# --------------------------------------------------------------------------
@tasks_router.get(
    "/persistent-status/{task_id}",
    response_model=JobStatus,
    tags=["Tasks - Persistent"],
)
async def get_task_status_persistent(
    task_id: UUID, session: AsyncSession = Depends(get_db_session)
):
    """
    Checks the persistent job result and status from the PostgreSQL database.
    This provides the final, non-volatile result.
    """
    # Use the TaskResult UUID to query the database
    job = await get_job_result_from_db(session, str(task_id))

    # 💡 Safety check for missing timestamps
    finished_at = job.finished_at.isoformat() if job.finished_at else None

    # Note: JobStatus is likely a Pydantic schema that expects these fields
    return {
        "task_id": str(job.task_id),
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "finished_at": finished_at,
        "result_data": job.result_data,
    }
