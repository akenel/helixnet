import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.core.constants import HelixEnum


# --- Enums for Schema Consistency ---
# We define a Pydantic-compatible version of the JobStatus enum
class JobStatusEnum(HelixEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


# =========================================================================
# 📦 JOB CREATE/SUBMIT (Input Schema) 📥
# =========================================================================
class JobSubmission(BaseModel):
    """
    Schema for the input request body when submitting a new job.
    Inherits from Pydantic's BaseModel, NOT SQLAlchemy's Base.
    """

    task_name: str = Field(
        ...,
        description="The Python function path for the Celery task to execute (e.g., 'tasks.process_report').",
    )
    input_data: Dict[str, Any] = Field(
        ..., description="The main JSON payload of parameters for the worker task."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_name": "src.tasks.process_data",
                "input_data": {
                    "source_url": "http://data.com/file.csv",
                    "format": "json",
                 "name": "➡️ Data Processing Job from user X",
                },
            }
        }
    )


# =========================================================================
# 📑 JOB READ (Output Schema) 📤
# =========================================================================
class JobRead(BaseModel):
    """
    Schema for the output response model, returned to the user, serialized from the ORM Job model.
    """

    job_id: uuid.UUID
    user_id: uuid.UUID
    status: JobStatusEnum  # Use the Pydantic-friendly enum
    celery_task_id: Optional[str] = None
    output_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None

    # CRITICAL: This enables Pydantic to read data directly from the SQLAlchemy ORM model instance
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# ⚙️ JOB UPDATE (Internal Schema for Worker/Service) 🛠️
# =========================================================================
class JobUpdate(BaseModel):
    """
    Schema used by the worker or internal services to update job fields in the database.
    """

    status: Optional[JobStatusEnum] = None
    celery_task_id: Optional[str] = None
    output_url: Optional[str] = None
    # We use Dict[str, Any] here because the actual result is stored in the ORM model as JSONB
    result_data: Optional[Dict[str, Any]] = None
    finished_at: Optional[datetime] = None


