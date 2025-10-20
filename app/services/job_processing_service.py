# ---app/services/job_processing_service.py 
#  Core Imports for Service ---
import uuid
import logging
import json
import io # Needed for streaming data to MinIO
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update
# Assuming these models/schemas exist based on your file structure
from app.db.models.job_model import Job 
from app.schemas.job_schema import JobUpdate # Used for type checking update_job_status_for_celery
# ---app/services/job_processing_service.py  Core Imports for Service ---
# 🚨 CRITICAL FIX: Assuming a synchronous version of this function exists in job_service.py
# from app.services.job_processing_service import get_job_by_id_sync 
from app.services.minio_service import minio_service # Sync MinIO client
# NOTE: Removed mock imports and internal status update functions.
logger = logging.getLogger(__name__)
# =========================================================================
# --- SYNCHRONOUS FUNCTIONS FOR CELERY WORKER CONTEXT ---
# These functions MUST use the standard synchronous SQLAlchemy session methods
# (e.g., db.get(), db.execute(), db.commit()).
# =========================================================================

def get_job_by_id_sync(db: Session, job_id: uuid.UUID) -> Optional[Job]:
    """
    Synchronously retrieves a Job model object from the database using its ID.
    
    This function is used exclusively by the Celery worker and the 
    JobProcessingService, which run in a synchronous environment.

    Args:
        db: The synchronous SQLAlchemy Session provided by the worker context.
        job_id: The UUID of the job to retrieve.

    Returns:
        The Job SQLAlchemy model instance, or None if not found.
    """
    logger.debug(f"DB SYNC: Attempting to retrieve job {job_id}.")
    
    # Use db.get() for efficient primary key lookup
    job_record = db.get(Job, job_id)
    
    if not job_record:
        logger.warning(f"DB SYNC: Job {job_id} not found.")
    
    return job_record


def update_job_status_for_celery(db: Session, job_id: uuid.UUID, update_data: Dict[str, Any]) -> None:
    """
    Synchronously updates the status and related data of a job.
    
    This function is used by the Celery task (app/tasks/job_tasks.py) 
    to manage the job lifecycle (e.g., PENDING -> IN_PROGRESS -> COMPLETED).

    Args:
        db: The synchronous SQLAlchemy Session provided by the worker context.
        job_id: The UUID of the job to update.
        update_data: A dictionary containing fields to update (e.g., status, finished_at).
    """
    # 1. Validate update data (optional but good practice)
    # Using the Pydantic schema to validate the input dictionary keys/types
    validated_data = JobUpdate(**update_data).model_dump(exclude_unset=True)
    
    logger.info(f"DB SYNC: Updating job {job_id} with status: {validated_data.get('status')}")

    # 2. Construct the update statement
    stmt = (
        update(Job)
        .where(Job.id == job_id)
        .values(**validated_data)
    )

    # 3. Execute the update
    result = db.execute(stmt)

    if result.rowcount == 0:
        logger.warning(f"DB SYNC: Update failed. Job {job_id} not found or no changes made.")
        # We don't raise here, as the task must mark itself as failed if necessary.
    else:
        # 4. Commit the transaction managed by the worker's 'with get_db_worker()' block
        # NOTE: The commit is technically handled by the outer 'with' block, 
        # but calling db.commit() here ensures the changes are persistent 
        # immediately before the function returns.
        db.commit() 
        logger.info(f"DB SYNC: Job {job_id} updated successfully.")


# =========================================================================
# --- ASYNCHRONOUS FUNCTIONS (for FastAPI API routes) ---
# NOTE: Other asynchronous job service functions (e.g., create, list, delete) 
# would be defined here, utilizing AsyncSession/await db.execute().
# =========================================================================

# Example placeholder for async methods that the API uses:
# async def create_job(db: AsyncSession, job_data: JobCreate) -> Job:
#     # ... implementation using await ...
#     pass















class JobProcessingService:
    """
    Service responsible for executing the core business logic of a job.
    Designed to run synchronously within a Celery worker.
    
    This service handles: DB read (Job record) using the provided session, 
    MinIO I/O (download/upload), and the core processing logic. 
    It DOES NOT update job status, as that is the responsibility of the 
    orchestrating Celery task.
    """
    
    def __init__(self):
        self.minio_client = minio_service

    def _mock_process_files(self, files: Dict[str, bytes]) -> Tuple[str, Dict[str, Any]]:
        """
        MOCK: Simulates the core job logic using the downloaded file contents.
        Returns the raw result JSON string (for upload) and the parsed result dict (for DB update).
        """
        logger.info("🎬 Starting mock processing...")
        
        # Simple processing simulation: combine content and context info
        content = files.get('content_key', b'').decode('utf-8', errors='ignore')
        context = files.get('context_key', b'').decode('utf-8', errors='ignore')
        
        # Calculate a simple result based on input data
        word_count = len(content.split())
        
        parsed_result = {
            "summary": "Processing completed successfully by Chuck Norris Logic.",
            "input_word_count": word_count,
            "context_loaded": bool(context),
            "output_format": "JSON",
            "process_id": f"PROC-{UUID.v4()}"
        }
        
        result_json_str = json.dumps(parsed_result, indent=2)
        
        logger.info("✅ Mock processing finished.")
        return result_json_str, parsed_result

    def process_uploaded_job(self, db: Session, job_id: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Main entry point for the worker task delegate.
        Retrieves job metadata, downloads files from MinIO, processes them,
        and uploads the final result artifact.

        Args:
            db: The synchronous SQLAlchemy session provided by the Celery task.
            job_id: The UUID string of the job.

        Returns:
            Tuple[bool, Optional[str], Optional[Dict[str, Any]]]: 
            (success_status, result_minio_key, result_payload)
        """
        job_uuid = UUID(job_id)
        
        # 1. Retrieve Job Metadata using the provided synchronous session
        logger.info(f"🔍 Fetching job metadata for {job_id} using sync session.")
        job_record = get_job_by_id_sync(db, job_uuid) 
        
        if not job_record:
            logger.error(f"Job {job_id} not found in DB. Returning failure.")
            # Return False, None, None if the job cannot be found
            return False, None, None 

        input_keys: Dict[str, str] = job_record.payload 
        
        # 2. Download Files from MinIO
        downloaded_files: Dict[str, bytes] = {}
        successful_downloads = True
        
        for key_name, minio_key in input_keys.items():
            logger.info(f"⬇️ Downloading file for {key_name} from MinIO key: {minio_key}")
            file_bytes = self.minio_client.download_artifact(minio_key)
            
            if file_bytes is None:
                logger.error(f"MinIO download failed for key: {minio_key}. Aborting downloads.")
                successful_downloads = False
                break
            
            downloaded_files[key_name] = file_bytes
            
        if not successful_downloads:
            # MinIO failure is considered a critical processing failure
            return False, None, None

        # 3. Core Processing and Upload
        result_minio_key = None
        result_payload = None
        
        try:
            # Core processing returns the JSON string (for upload) and dict (for DB)
            result_json_str, result_payload = self._mock_process_files(downloaded_files)
            result_bytes = result_json_str.encode('utf-8')
            
            # Define the output MinIO key: jobs/{user_id}/{job_id}/result.json
            output_object_name = f"jobs/{job_record.owner_id}/{job_id}/result.json"
            
            # 4. Upload Result Artifact to MinIO
            logger.info(f"⬆️ Uploading result artifact to MinIO: {output_object_name}")
            
            # Use io.BytesIO to simulate a file stream for the synchronous MinIO upload
            result_stream = io.BytesIO(result_bytes)
            
            result_minio_key = self.minio_client.upload_artifact(
                file_data=result_stream,
                object_name=output_object_name,
                content_type="application/json"
            )
            
            if not result_minio_key:
                # If upload fails, raise an exception to trigger the outer task's retry/failure logic
                raise Exception("Failed to upload final artifact to MinIO.")
            
        except Exception as e:
            logger.error(f"Critical error during core processing or artifact upload for {job_id}: {e}")
            # Failure occurred: return False and no results
            return False, None, None

        # 5. Return Success Status and Artifact details
        logger.info(f"✨ Job {job_id} completed successfully. Artifact stored at: {result_minio_key}")
        return True, result_minio_key, result_payload

job_processor = JobProcessingService()
