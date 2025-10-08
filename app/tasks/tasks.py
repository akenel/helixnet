# 🥊 Core Celery Tasks - The Heavy Lifters
# Defines the asynchronous tasks that perform the long-running business logic
# and update the job status in the Postgres Ledger.

import logging
import time
from uuid import UUID
from celery import current_task
from sqlalchemy.orm import Session

# Import the Celery app instance
from app.tasks.celery_app import celery_app 

# Import the necessary DB utility, Service, and Schemas
from app.tasks.db_utils import get_db_worker 
from app.api.services.job_service import JobService
from app.schemas.job import JobStatus, JobUpdate
from app.db.models.job import JobModel

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 🛡️ Internal DB Helper Function (Worker Trust)
# --------------------------------------------------------------------------

def _update_job_status(
    db: Session, 
    job_id: UUID, 
    status: JobStatus, 
    celery_task_id: str, 
    output_url: str = None, 
    result_data: dict = None
):
    """
    Internal function for the worker to reliably update the job's state in the DB.
    It fetches the job and applies the update via the JobService.
    """
    # 1. Fetch the job using the JobService
    # NOTE: The worker trusts the job_id, so we don't enforce user_id here.
    db_job = db.query(JobService.model).filter(JobService.model.id == job_id).first()
    
    if not db_job:
        logger.error(f"Job ID {job_id} not found in database for update. Task aborting.")
        return

    # 2. Create the JobUpdate schema object
    job_update_data = JobUpdate(
        status=status,
        celery_task_id=celery_task_id,
        output_url=output_url,
        result_data=result_data
    )

    # 3. Update using the service layer
    JobService.update_job(db, db_job, job_update_data)
    logger.info(f"DB UPDATE: Job {job_id} set to status: {status.value}")


# --------------------------------------------------------------------------
# 💥 Core Task: The Roundhouse Kick
# --------------------------------------------------------------------------

@celery_app.task(bind=True)
def send_processing_task(self, job_id: str):
    """
    Simulates a long-running, asynchronous AI data processing task.
    This task is triggered by the API and is responsible for all DB status updates.
    """
    job_uuid = UUID(job_id)
    celery_task_id = self.request.id
    
    # 1. Get a fresh database session for this worker task
    db_generator = get_db_worker()
    db: Session = next(db_generator)

    try:
        # --- Pre-Step: Retrieve Initial Job Details ---
        # We need the full job model to get input_file_path and other config
        initial_job = db.query(JobModel).filter(JobModel.id == job_uuid).first()
        if not initial_job:
            raise ValueError(f"Initial Job {job_id} not found in DB.")
        
        logger.info(f"TASK START: Job {job_id} (Celery ID: {celery_task_id}) for template: {initial_job.template_name}.")
        
        # --- Step 1: Update Job Status to PROCESSING ---
        _update_job_status(db, job_uuid, JobStatus.PROCESSING, celery_task_id)
        
        # --- Step 2: The Core Work (Simulating LLM Call/Heavy Compute) ---
        
        # Update Celery state for visibility
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'Fetching data from MinIO...'})
        time.sleep(1) 
        
        current_task.update_state(state='PROGRESS', meta={'progress': 50, 'message': 'Calling LLM for transformation...'})
        time.sleep(5) # Simulate 5 seconds of heavy processing

        # Simulate final artifact details
        output_minio_url = f"minio://results/{job_id}/final_output.json"
        final_result_data = {
            "processed_template": initial_job.template_name,
            "output_path": output_minio_url,
            "processed_at": datetime.now().isoformat()
        }

        # --- Step 3: Update Job Status to COMPLETE ---
        _update_job_status(
            db, 
            job_uuid, 
            JobStatus.COMPLETE, 
            celery_task_id, 
            output_url=output_minio_url,
            result_data=final_result_data
        )
        
        logger.info(f"TASK COMPLETE: Job {job_id} finished. Result URL: {output_minio_url}")
        
        return {"status": "success", "result_url": output_minio_url}

    except Exception as e:
        error_details = {"error_message": str(e), "task": "send_processing_task"}
        logger.error(f"Task {job_id} FAILED: {e}")
        
        # Update job status to FAILED in case of any exception
        _update_job_status(db, job_uuid, JobStatus.FAILED, celery_task_id, result_data=error_details)
        
        # Re-raise the exception to allow Celery's retry mechanism to kick in
        raise 
    
    finally:
        # CRITICAL: Ensure the session is closed regardless of success or failure
        next(db_generator, None)


# --------------------------------------------------------------------------
# 🌼 Health Check Tasks (Sanity)
# --------------------------------------------------------------------------

@celery_app.task(name="app.tasks.tasks.say_hello")
def say_hello():
    """Periodic task that says hello."""
    logger.info("👋 Hello from Celery Beat!")
    return "👌️ Hello from Celery!"

@celery_app.task(name="app.tasks.tasks.system_healthcheck")
def system_healthcheck():
    """Periodic system health check task."""
    logger.info("❤️  Celery System Healthcheck: OK")
    return "🐇️ System healthy"
