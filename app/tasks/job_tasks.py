# app/tasks/job_tasks.py
# 🥊 Core Celery Tasks - The Heavy Lifters
# =========================================================================

from datetime import datetime, UTC # 🚨 CN FIX: Ensure UTC is imported for timezones
import logging
import time
from uuid import UUID
from celery import current_task
from sqlalchemy.orm import Session # Required for the synchronous DB session

# 🧱 --- Core Imports ---
from app.tasks.celery_app import celery_app

# In /code/app/tasks/job_tasks.py

# 🚨 CRITICAL FIX: Use the actual function name defined in database.py
from app.db.database import get_db_session_sync as get_db_worker
from app.db.models.job_model import Job
from app.schemas.job_schema import JobUpdate # 🚨 CRITICAL FIX: Need the Pydantic schema for updates
from app.services.job_service import update_job_status_for_celery # 🚨 CRITICAL FIX: Use the dedicated sync service

logger = logging.getLogger(__name__)

# In /code/app/tasks/job_tasks.py (The process_data function)

@celery_app.task(bind=True, name='app.tasks.process_data')
def process_data(self, job_id: str):
    job_uuid = UUID(job_id)
    celery_task_id = self.request.id

    # 1. 💥 CN FIX: Use the 'with' statement for the synchronous context manager
    # The 'with' block manages the session (open, commit/rollback, close).
    with get_db_worker() as db: 
        try:
            logger.info(
                f"TASK START 🪡️ Job {job_id} (Celery ID: {celery_task_id})."
            )
            
            # --- Step 1: Update Job Status to PROCESSING ---
            status_update_data = {
                "status": "PROCESSING",
                "celery_task_id": celery_task_id
            }
            update_job_status_for_celery(db, job_uuid, status_update_data)


            # --- Step 2: The Core Work (Simulating LLM Call/Heavy Compute) ---
            current_task.update_state(state="PROGRESS", meta={"progress": 10, "message": "🚋️ Fetching data from MinIO..."})
            time.sleep(1)

            current_task.update_state(state="PROGRESS", meta={"progress": 50, "message": "🦄️ Calling LLM for transformation..."})
            time.sleep(5) # Simulate 5 seconds of heavy processing

            # Simulate final artifact details
            output_minio_url = f"minio://results/{job_id}/final_output.json"
            final_result_data = {
                "output_path": output_minio_url,
                "processed_at": datetime.now(UTC).isoformat(),
            }

            # -----------------------------------------------
            # --- Step 3: Update Job Status to SUCCESS (INSIDE THE TRY BLOCK) ---
            # -----------------------------------------------
            status_update_data = {
                "status": "COMPLETED",
                "output_url": output_minio_url,
                "result_data": final_result_data,
                "finished_at": datetime.now(UTC),
            }
            
            update_job_status_for_celery(db, job_uuid, status_update_data)

            logger.info(
                f"TASK COMPLETE: Job {job_id} finished. 🎁️ Result URL: {output_minio_url}"
            )

            return {"status": "success", "result_url": output_minio_url}

        except Exception as e:
            error_details = {"error_message": str(e), "task": "process_data"}
            logger.error(f"Task {job_id} FAILED: {e}")

            # Update job status to FAILED in case of any exception
            status_update_data = {
                "status": "FAILURE",
                "result_data": error_details,
                "finished_at": datetime.now(UTC),
            }
            # This call uses the session managed by the 'with' block
            update_job_status_for_celery(db, job_uuid, status_update_data)

            # Re-raise the exception to allow Celery's retry mechanism to kick in
            raise

    # 💥 CN ACTION: Delete the entire 'finally' block! 
    # The 'with get_db_worker() as db:' handles all session closing/rollback/commit.
# --------------------------------------------------------------------------
# 🌼 Health Check Tasks (Sanity)
# --------------------------------------------------------------------------

# 🚨 CN FIX: Simplified task imports/names for clarity.
@celery_app.task(name="app.tasks.say_hello")
def say_hello():
    """Periodic task that says hello."""
    logger.info("👋 Hello from Celery Beat!")
    return "👌️ Hello from Celery!"


@celery_app.task(name="app.tasks.system_healthcheck")
def system_healthcheck():
    """Periodic system health check task."""
    logger.info("❤️  Celery System Healthcheck: OK")
    return "🐇️ System healthy"