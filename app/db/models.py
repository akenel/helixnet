# =========================================================================
# ⚔️ CENTRAL ORM MODELS (CHUCK'S DATA ENGINE)
# This file defines and registers all core SQLAlchemy ORM models,
# ensuring data persistence aligns with the Pydantic schemas.
# =========================================================================
from uuid import uuid4
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List

from sqlalchemy import String, DateTime, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

# --- Project Imports ---
# Assuming Base is located in app.db.base and User model is available
from app.db.base import Base # Base class for ORM models
# We need to import the JobStatus Enum for strong typing at the DB level
from app.schemas.job import JobStatus

# --- Placeholder for User Model Import (required for FK) ---
# NOTE: The User model MUST be defined elsewhere and imported here,
# or defined directly below if it is not in its own file.
# For this example, we assume User is available for the relationship.
try:
    from .user import User
except ImportError:
    # Minimal placeholder to allow the file to run if User is defined elsewhere
    class User:
        pass


# --- 1. JOB RESULT MODEL ('job_results' table) ---

class JobResult(Base):
    """
    The central ORM model for asynchronous jobs, tracking definition, status,
    and output. This maps directly to the Job Pydantic schema.
    """
    __tablename__ = "job_results"

    # Core Identifiers
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), # Links to the user who started the job
        nullable=False,
        index=True
    )
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="The unique ID used by the Celery worker for tracing."
    )

    # Job Definition (Inputs from JobBase/JobCreate)
    input_file_path: Mapped[str] = mapped_column(String, nullable=False, comment="Path to the input artifact in MinIO.")
    template_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="The name of the processing template.")
    initial_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, default={})


    # Status and Output (Outputs from JobUpdate)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", create_type=False),
        default=JobStatus.PENDING,
        nullable=False,
        comment="Current lifecycle status of the job (PENDING, COMPLETE, FAILED, etc.)."
    )
    output_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, comment="URL for the final output artifact.")
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Structured JSON output summary from the worker (for quick display)."
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ORM Relationship
    user: Mapped["User"] = relationship(back_populates="jobs")

    def __repr__(self) -> str:
        return (
            f"<JobResult(id='{self.id}', status='{self.status.value}', "
            f"template='{self.template_name}')>"
        )

# --- 2. TASK RESULT MODEL ('task_results' table) ---

class TaskResult(Base):
    """
    ORM model for the 'task_results' table, typically used by Celery's
    SQLAlchemy result backend for low-level task tracking.
    """
    __tablename__ = "task_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Celery's low-level status
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    date_done: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    traceback: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<TaskResult(task_id='{self.task_id}', status='{self.status}')>"

# Define __all__ for clean imports
__all__ = ['User', 'JobResult', 'TaskResult']
