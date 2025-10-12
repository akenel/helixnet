import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, TYPE_CHECKING

# 📚 SQLAlchemy Imports
from sqlalchemy import ForeignKey, Enum, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Using PostgreSQL specific types for optimized performance
from sqlalchemy.dialects.postgresql import UUID, JSONB

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base # ✅ Corrected Base import

# 🔗 Type Checking for Relationships
if TYPE_CHECKING:
    from .user_model import User
    from .job_model import Job


# =========================================================================
# 🎯 ENUMS: TASK STATUS 📜
# =========================================================================
class TaskStatus(str, enum.Enum):
    """
    Defines the possible states for a micro-task within a larger job.
    """
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


# =========================================================================
# 📝 TASK RESULT ORM MODEL
# =========================================================================
class TaskResult(Base):
    """
    Stores the detailed result of an individual, asynchronous task (micro-task) 
    that contributes to a main Job.
    """

    __tablename__ = "task_results"
    __allow_unmapped__ = False

    # --- Primary Key & Foreign Keys ---

    # 💥 Primary Key
    task_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique UUID for this specific task result.",
    )

    # 🔗 Foreign Key to Job (One Job has many TaskResults)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey( "jobs.job_id", ondelete="CASCADE", ),
        doc="The UUID of the parent Job.",
    )

    # 🔗 Foreign Key to User (One User initiated this Task/Job)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id",ondelete="CASCADE",),
        doc="The UUID of the user who initiated the parent job.",
    )
    
    # --- Status and Output Fields ---

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.QUEUED,
        doc="Current state of the micro-task.",
    )
    
    task_name: Mapped[str] = mapped_column(
        String(255),
        doc="Name of the function or worker task executed.",
    )
    
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Structured JSON output/metadata from the task execution.",
    )
    
    # --- Timestamps ---

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the task result record was created.",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC), 
        doc="When the task was last updated.",
    )
    
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the task hit a terminal status (COMPLETED/FAILED).",
    )

    # --- Relationships ---

    # Link back to the Job (Many-to-One)
    job: Mapped["Job"] = relationship(back_populates="task_results")

    # Link back to the User (Many-to-One)
    user: Mapped["User"] = relationship(back_populates="task_results")


    def __repr__(self) -> str:
        return f"<TaskResult(task_result_id='{self.task_result_id}', status='{self.status.value}', job_id='{self.job_id}')>"
