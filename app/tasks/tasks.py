# app/tasks/tasks.py
from celery import shared_task
from typing import Dict, Any
import logging, time, uuid
from datetime import datetime, UTC
"""
Celery task definitions for background processing.
"""
from app.db.database import get_db_session_sync 
from app.schemas.jobs import JobStatus 
from app.tasks.celery_app import celery_app
from app.db.database import get_db_session_sync
from app.services.job_service import update_job_status
# app/tasks/tasks.py (The Corrected Celery Task)

# NOTE: Assuming update_job_status_sync is defined and imported
from app.services.job_service import update_job_status_sync 
from app.schemas.jobs import JobStatus 
# ... other imports ...
# 
logger = logging.getLogger(__name__)
#

@shared_task(name="app.tasks.tasks.process_job")
def process_job(job_id: str, user_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    job_uuid = uuid.UUID(job_id)
    
    try:
        with get_db_session_sync() as db:
            logger.info(f"🚀 Starting job {job_id} for user {user_id}.")
            
            # 🌟 FIX: Pass the JobStatus Pydantic schema object
            running_status_obj = JobStatus(job_id=job_uuid, status="RUNNING")
            update_job_status_sync(db, job_uuid, running_status_obj) # Use sync function

        # Simulated work
        time.sleep(3)

        final_result = {
            # ... result data ...
        }

        with get_db_session_sync() as db:
            logger.info(f"✅ Job {job_id} finished successfully.")
            
            # 🌟 FIX: Pass the JobStatus Pydantic schema object with result data
            success_status_obj = JobStatus(
                job_id=job_uuid, 
                status="SUCCESS", 
                result_data=final_result # Include the result
            )
            update_job_status_sync(db, job_uuid, success_status_obj) # Use sync function

        return final_result

    except Exception as e:
        error_msg = {"error": str(e)} # Status is not needed here
        logger.error(f"❌ Job {job_id} failed: {str(e)}")

        with get_db_session_sync() as db:
            # 🌟 FIX: Pass the JobStatus Pydantic schema object with error data
            failure_status_obj = JobStatus(
                job_id=job_uuid, 
                status="FAILURE", 
                result_data=error_msg # Include the error message
            )
            update_job_status_sync(db, job_uuid, failure_status_obj) # Use sync function

        raise
# health checks for sanity checks 
@shared_task
def sanity_check_task() -> Dict[str, str]:
    """Simple task to verify Celery worker is responsive."""
    return {"status": "🌼️ Celery worker is healthy"}
@shared_task
def say_hello():
    """Periodic task that says hello."""
    return "👌️ Hello from Celery!"
@shared_task
def system_healthcheck():
    """Periodic system health check task."""
    return {"status": "🐇️ System healthy"}

@celery_app.task(name="app.tasks.process_job") 
def process_job(job_id: str, user_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:

    """Simulates a complex AI workflow task."""
    job_uuid = uuid.UUID(job_id)

    # 1. Update status to RUNNING
    with get_db_session_sync() as db:
        logger.info(f"💰️ Task {job_id} starting.")
        
        # Use JobStatus schema for consistency, passing only what changes
        running_status = JobStatus(job_id=job_uuid, status="RUNNING")
        update_job_status_sync(db, job_uuid, running_status)
    
    # 2. Simulate AI work (time-consuming operation)
    time.sleep(5)    
    
    # 3. Update status to SUCCESS and add dummy result
    final_result_data = {
        "status": "processed",
        "timestamp": datetime.now(UTC).isoformat(),
        "job_id": job_id,
        "ai_output": "Structured JSON Result Placeholder"
    }
    
    with get_db_session_sync() as db:
        logger.info(f"Task {job_id} finished successfully.")
        
        # Use JobStatus schema, providing the final status and result
        success_status = JobStatus(
            job_id=job_uuid, 
            status="SUCCESS", 
            result_data=final_result_data
        )
        update_job_status_sync(db, job_uuid, success_status)

@celery_app.task(name="app.tasks.tasks.say_hello")
def say_hello():
    logger.info("👋 Hello from Celery Beat!")
    return "Hello"
@celery_app.task(name="app.tasks.tasks.system_healthcheck")
def system_healthcheck():
    logger.info("❤️  Celery System Healthcheck: OK")
    return "OK"