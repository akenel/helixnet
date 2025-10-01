"""
SQLAlchemy Model for Persistent Job Results (Phase 2.0)

This model links asynchronous Celery job IDs and results back to the initiating user.
It uses modern SQLAlchemy 2.0 'Mapped' style for clarity and type safety.
"""
import uuid
from datetime import datetime, UTC # Use modern UTC constant
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Deferred import for type hinting to prevent circular dependencies
    from app.db.models.user import User

class JobResult(Base):
    """Represents the persistent record of a Celery background job."""
    
    __tablename__ = "job_results"

    # --- Primary Key ---
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # --- Foreign Key and Relationship to User ---
    
    # CRITICAL: Foreign Key definition (links to users table 'id')
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), # Cascade delete for cleanup
        nullable=False
    )
    
    # CRITICAL: Relationship property for ORM access
    # 'back_populates="job_results"' completes the two-way link to User model
    user: Mapped["User"] = relationship(
        back_populates="job_results"
    )

    # --- Task Information (FIXED: Converted to Mapped style) ---
    task_id: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        doc="The UUID assigned by Celery for this specific task execution."
    )
    
    task_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="The python function path of the task (e.g., app.tasks.tasks.say_hello)."
    )
    
    # --- Status and Results ---
    status: Mapped[str] = mapped_column(
        String(50), 
        default="PENDING",
        doc="Current status of the task (PENDING, STARTED, SUCCESS, FAILURE, etc.)."
    )
    
    result_data: Mapped[str | None] = mapped_column(
        Text, 
        nullable=True,
        doc="JSON or string representation of the final task output."
    )
    
    # --- Timestamps (FIXED: Converted to Mapped style) ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.now(UTC),
        doc="Time the record was created/task was submitted."
    )
    
    # Optional field for when the task completed
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        doc="Time the task moved to a final state (SUCCESS/FAILURE)."
    )

    def __repr__(self) -> str:
        """Friendly representation for debugging."""
        return f"<JobResult(id='{self.id}', user_id='{self.user_id}', status='{self.status}')>"
