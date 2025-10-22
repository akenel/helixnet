# File: app/db/models/message_tasks_model.py
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
# Use mapped_column for 2.0 style consistency
from sqlalchemy import String, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column 
from .base import Base

import enum

class TaskType(enum.Enum):
    """Defines the type of task the message relates to."""
    EXECUTION = "execution"  # e.g., run a job/pipeline
    NOTIFICATION = "notification" # e.g., send an alert
    HEALTH_CHECK = "health_check" # e.g., check service status
    CONFIGURATION = "configuration" # e.g., update settings
    SCHEDULING = "scheduling" # e.g., set up a cron job

class TaskStatus(enum.Enum):
    """Defines the status of the background task."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageTaskModel(Base):
    """
    Represents a record of a task sent to or handled by a message broker (like Celery/RabbitMQ).
    This serves as a ledger for background processes initiated by the API.
    """
    __tablename__ = 'message_tasks'

    # ----------------------------------------------------
    # COLUMNS (Use mapped_column for 2.0 style consistency)
    # ----------------------------------------------------
    
    # Primary Key
    id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    # Ownership and Context (Use mapped_column)
    initiator_user_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, comment="User who initiated the task")

    # Core Task Definition (Use mapped_column)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="The function/task name")
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.EXECUTION, nullable=False)
    
    # Message Broker IDs (Use mapped_column)
    broker_task_id: Mapped[str | None]  = mapped_column(String(255), nullable=True, unique=True, index=True, comment="The ID assigned by the message broker")

    # Status and Results (Use mapped_column)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Short message about success/failure")
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Detailed error information")
    
    # Input/Output Data (Use mapped_column)
    input_args_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON string of input arguments")
    output_result_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON string of the task's return value")

    # Timestamps (Use mapped_column)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_to_broker_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="When queued")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="When worker picked up")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="When completed")

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------
    
    # FIX: Rename the property to 'owner' to satisfy the missing property error.
    # The back_populates should now be 'initiated_message_tasks' based on your comment.
    owner: Mapped["UserModel"] = relationship(
        "UserModel", 
        back_populates="initiated_message_tasks",
        foreign_keys=[initiator_user_id] # Explicitly define the FK for clarity
    )

    def __repr__(self):
        return f"<MessageTaskModel(id='{self.id}', name='{self.task_name}', status='{self.status}')>"