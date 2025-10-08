# =========================================================================
# 🛡️ JOB SCHEMAS - THE DATA CONTRACT (CHUCK'S LEDGER)
# This single file defines the lifecycle and structure for all asynchronous
# job transactions, ensuring data integrity across the API, DB, and Workers.
# =========================================================================

from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- 🎯 THE JOB STATUS ENUM (THE LEDGER CONTRACT) ---

class JobStatus(str, Enum):
    """
    Defines the possible states for an asynchronous job.
    This Enum acts as the single source of truth for job lifecycle:
    API (Creation) -> DB (Storage) -> Worker (Processing).
    """
    PENDING = "PENDING"      # Job submitted, waiting for worker pickup.
    PROCESSING = "PROCESSING"  # Worker has started executing the task.
    COMPLETE = "COMPLETE"    # Job finished successfully.
    FAILED = "FAILED"        # Job finished with an error.
    CANCELLED = "CANCELLED"  # Job was manually cancelled or revoked.
    RETRYING = "RETRYING"    # Job failed but is scheduled for another attempt.

# --- 🧱 BASE SCHEMAS (CORE JOB DEFINITION) ---

class JobBase(BaseModel):
    """Base schema for data that defines the job's intention and necessary inputs."""

    # 📁 CRITICAL: The path to the artifact uploaded to MinIO
    input_file_path: str = Field(..., description="Path to the input artifact in MinIO or a mounted volume.")

    # 🧠 CRITICAL: Which LLM template/logic should the worker execute?
    template_name: str = Field(..., description="The name of the processing template (e.g., 'financial_summary').")

    # Optional parameters for the processing logic
    initial_config: Optional[Dict[str, Any]] = Field(
        None, description="Arbitrary configuration data for the worker processing task."
    )

class JobCreate(JobBase):
    """Schema used by the POST /jobs endpoint to initiate a task."""
    pass

# To satisfy the previous import error:
JobSubmission = JobCreate


# --- 💎 FULL JOB SCHEMA (READ/VIEW CONTRACT) ---

class Job(JobBase):
    """The full schema returned to the client on GET /jobs/{id} or POST /jobs."""
    id: UUID = Field(..., description="Unique UUID assigned to the job.")
    user_id: UUID = Field(..., description="The UUID of the user who initiated the job.")
    celery_task_id: Optional[str] = Field(None, description="The internal Celery ID for tracing the worker task.")
    status: JobStatus
    output_url: Optional[str] = Field(None, description="URL pointing to the final result artifact in MinIO.")
    result_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured JSON output from the job (for quick display)."
    )
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None # When the job status transitioned to COMPLETE/FAILED/CANCELLED

    # ORM Mode: CRITICAL to read SQLAlchemy attributes (columns)
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True  # Ensures the status is returned as a string
    )


# --- 🔄 JOB UPDATE SCHEMAS (INTERNAL WORKER CONTRACT) ---

class JobUpdate(BaseModel):
    """
    Schema used by the Celery worker and internal services to update job fields.
    This is how the job status transitions from PENDING -> PROCESSING -> COMPLETE/FAILED.
    """
    status: Optional[JobStatus] = None # 💥 The new, current status
    celery_task_id: Optional[str] = None # 🔗 The ID used by Celery for tracking
    output_url: Optional[str] = None # 📦 URL pointing to the final result artifact in MinIO
    result_data: Optional[Dict[str, Any]] = None # 💎 Structured JSON output (for quick lookup)
    finished_at: Optional[datetime] = None # Set when job completes or fails

    model_config = ConfigDict(
        use_enum_values=True # Ensures the Enum value (string) is used in JSON output
    )
