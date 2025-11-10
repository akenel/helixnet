# -------------------------------------------------------------------------
import uuid
# Assuming these are available and configured:
from src.tasks.celery_app import celery_app
from src.tasks.db_utils import get_db_worker # Sync DB context manager for worker tasks
from src.db.models.job_model import JobModel # For Job.Status enum
# The synchronous DB update utility we just created
from src.services.job_service import update_job_status_for_celery
# The core logic service
from src.services.job_processing_service import job_processor 

from datetime import datetime, UTC, timezone
import logging
from typing import Dict, Any, Tuple
from uuid import UUID
from celery import current_task

# --- CELERY CORE SETUP ---
from src.tasks.celery_app import celery_app 

# --- DB & Service Imports ---
# 🚨 CRITICAL FIX: Use the actual function name defined in database.py
from src.db.database import get_db_session_sync as get_db_worker
# Dedicated sync service function for job status updates (using Pydantic schemas)
from src.services.job_service import update_job_status_for_celery 
# The new core logic service which handles MinIO I/O
from src.services.job_processing_service import job_processor 

logger = logging.getLogger(__name__)

# =========================================================================
# --- 🎯 CELERY TASK DEFINITIONS (CHUCK NORRIS TASK FORCE) ---
# =========================================================================

@celery_app.task(bind=True, name="process_job", max_retries=3, default_retry_delay=60)
def process_job(self, job_id: str):
    """
    The main Celery task responsible for orchestrating job execution.
    It manages the synchronous SQLAlchemy session and delegates core processing 
    (MinIO download/upload/LLM logic) to the JobProcessingService.

    Args:
        job_id: The UUID (as a string) of the job to process.
    """
    job_uuid = UUID(job_id)
    celery_task_id = self.request.id
    
    # 1. 💥 CN FIX: Use the 'with' statement for the synchronous DB session manager.
    # This automatically handles session creation, commit, rollback on exception, and closing.
    with get_db_worker() as db:
        try:
            attempt_info = f"Attempt: {self.request.retries + 1}"
            logger.info(f"TASK START 🪡️ Job {job_id} (Celery ID: {celery_task_id}). {attempt_info}")

            # --- Step 1: Update Job Status to IN_PROGRESS (MANDATORY START) ---
            status_update_data = {
                "status": "IN_PROGRESS",
                "celery_task_id": celery_task_id,
            }
            update_job_status_for_celery(db, job_uuid, status_update_data)
            
            # --- Optional: Report initial progress to the client ---
            current_task.update_state(
                state="PROGRESS",
                meta={"progress": 5, "message": "Starting core processing and MinIO operations..."}
            )

            # --- Step 2: Delegate Core Processing to the dedicated service ---
            # NOTE: We assume job_processor.process_uploaded_job is updated to accept the DB session 
            # and returns the outcome tuple: (success, result_minio_key, result_data)
            success, result_minio_key, result_data = job_processor.process_uploaded_job(db, job_id)
            
            if not success:
                 # Raise an exception to trigger the FAILURE block below
                raise Exception("Job processing service returned failure due to internal error.")
            
            # --- Step 3: Update Job Status to COMPLETED ---
            status_update_data = {
                "status": "COMPLETED",
                "output_url": result_minio_key, # Store the MinIO artifact key
                "result_data": result_data,      # Store the parsed result payload
                "finished_at": datetime.now(tz=timezone.utc),
            }

            update_job_status_for_celery(db, job_uuid, status_update_data)

            logger.info(
                f"TASK COMPLETE: Job {job_id} finished. 🎁️ Result URL: {result_minio_key}"
            )

            return {"status": "success", "result_url": result_minio_key}

        except Exception as e:
            # --- Step 4: Handle Failure and Retry Logic ---
            error_details = {"error_message": str(e), "task_id": celery_task_id}
            logger.error(f"❌ Job {job_id} FAILED: {e}")

            # Update job status to FAILURE
            status_update_data = {
                "status": "FAILURE",
                "result_data": error_details,
                "finished_at": datetime.now(tz=timezone.utc),
            }
            update_job_status_for_celery(db, job_uuid, status_update_data)
            
            # Re-raise to allow Celery's retry mechanism (max_retries=3 defined in decorator)
            # This is the proper way to trigger retries in Celery within a try/except block.
            raise self.retry(exc=e)

# --------------------------------------------------------------------------
# 🌼 Health Check Tasks (Sanity)
# --------------------------------------------------------------------------

@celery_app.task(name="src.tasks.say_hello")
def say_hello():
    """Periodic task that says hello."""
    logger.info("👋 Hello from Celery Beat!")
    return "👌️ Hello from Celery!"


@celery_app.task(name="src.tasks.system_healthcheck")
def system_healthcheck():
    """Periodic system health check task."""
    logger.info("❤️  Celery System Healthcheck: OK")
    return "🐇️ System healthy"

# -------------------------------------------------------------------------
# Usage Note for API Router:
# To enqueue this task from an asynchronous FastAPI endpoint, use:
# process_job.delay(str(job_record.id))

# --- Celery Task Definition ---

@celery_app.task(
    bind=True, 
    name="process_job", 
    max_retries=3, 
    default_retry_delay=60, # Retry after 60 seconds
    autoretry_for=(Exception,), # Retry on any general exception
    queue="job_processing"
)
def process_job(self, job_id: str) -> bool:
    """
    Main Celery task for processing an individual job. 
    It orchestrates the entire lifecycle of the job execution.
    """
    job_uuid = uuid.UUID(job_id)
    logger.info(f"Starting Celery task execution for Job ID: {job_id}")
    
    # Update Status: IN_PROGRESS
    try:
        # Use the synchronous DB context for the worker
        with get_db_worker() as db:
            update_job_status_for_celery(
                db, 
                job_uuid, 
                {'status': JobModel.Status.IN_PROGRESS, 'started_at': datetime.utcnow()}
            )
        logger.info(f"Job {job_id} status updated to IN_PROGRESS.")
    except Exception as e:
        # Critical failure: cannot update status or get DB session.
        logger.error(f"FATAL: Could not update job {job_id} to IN_PROGRESS. Retrying. Error: {e}")
        # Signal Celery to retry the task immediately if this setup fails
        raise self.retry(exc=e) 

    success = False
    result_minio_key = None
    result_content_payload = None
    
    # Core Processing Logic
    try:
        # The processing service uses its own logic and the synchronous DB session 
        # (retrieved inside the processing service via get_job_by_id_sync)
        with get_db_worker() as db:
            success, result_minio_key, result_content_payload = job_processor.process_uploaded_job(db, job_id)
            
        if not success:
            raise RuntimeError("Job processing service reported failure without raising a specific exception.")
        
    except Exception as e:
        logger.error(f"Core job processing failed for {job_id}: {e}", exc_info=True)
        # The job processing service should handle its own FAILED update on critical failure,
        # but we ensure the status is FAILED here if an unexpected exception propagated.
        success = False
        
    # Final Status Update (Completed or Failed)
    final_status = JobModel.Status.COMPLETED if success else JobModel.Status.FAILED
    update_data = {
        'status': final_status, 
        'finished_at': datetime.utcnow(),
        'result_path': result_minio_key,
        'result_content': result_content_payload
    }
    
    try:
        with get_db_worker() as db:
            update_job_status_for_celery(db, job_uuid, update_data)
        
        if success:
            logger.info(f"✨ Job {job_id} completed and final status saved.")
        else:
            logger.warning(f"❌ Job {job_id} failed and final status saved.")
            
    except Exception as e:
        logger.error(f"CRITICAL: Failed to save final status ({final_status}) for job {job_id}. Error: {e}")
        # If we cannot save the final status, we should retry to avoid data loss.
        raise self.retry(exc=e, countdown=300) # Longer retry for saving final state

    return success
