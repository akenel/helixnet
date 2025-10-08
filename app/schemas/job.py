from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# --- Core Job Status Enum --- Job Schemas and Status  - app/schemas/job.py
class JobStatus(str, Enum):
    """
    Defines the possible states for an asynchronous job.
    This Enum acts as the single source of truth for job lifecycle.
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


# --- Pydantic Schemas for API Interaction ---

class JobBase(BaseModel):
    """Base schema for job data."""
    # This might include fields passed during submission, e.g.:
    input_file_path: str = Field(..., description="Path to the input artifact in MinIO or a mounted volume.")
    template_name: str = Field(..., description="The name of the processing template (e.g., 'summarize_report').")


class JobCreate(JobBase):
    """Schema for creating a new job (used in the POST request body)."""
    # The API will automatically fill in user_id, status, etc.
    pass

class JobUpdate(BaseModel):
    """Schema for updating job fields (e.g., used by the worker or an admin API)."""
    status: Optional[JobStatus] = None
    output_url: Optional[str] = None
    celery_task_id: Optional[str] = None
    
    class Config:
        use_enum_values = True # Ensures the Enum value (string) is used in JSON output


class Job(JobBase):
    """Schema for returning a job response to the client."""
    id: UUID
    user_id: UUID
    celery_task_id: Optional[str] = None
    status: JobStatus
    output_url: Optional[str] = Field(None, description="URL pointing to the final result artifact in MinIO.")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True
# app/schemas/job.py: Defines the Python Enum for 
# job status (the states are crucial) and the Pydantic schemas used for requests and responses.