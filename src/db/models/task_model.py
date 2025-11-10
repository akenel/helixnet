# File: app/db/models/task_model.py
# Updated: October 21, 2025
from sqlalchemy.dialects.postgresql import UUID
import uuid

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from .base import Base

import enum

class TaskPriority(enum.Enum):
    """Defines the priority levels for a Task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskModel(Base):
    """
    Represents an individual, actionable task within a Job or Pipeline.
    Tasks are the discrete units of work managed by users or workers.
    """
    __tablename__ = 'tasks'

    # Primary Key
    id: Mapped[uuid.UUID]  = Column(UUID(as_uuid=True), primary_key=True, index=True)

    # Core Task Fields
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str | None] = Column(Text, nullable=True)
    status: Mapped[str] = Column(String(50), default="todo", nullable=False, comment="e.g., 'todo', 'in_progress', 'done'")
    priority: Mapped[TaskPriority] = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    is_completed: Mapped[bool] = Column(Boolean, default=False, nullable=False)

    # Foreign Key to User (Task Owner/Assignee)
    owner_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Foreign Key to Job (Optional)
    job_id:  Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
  # Timestamps and Dates
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    due_date: Mapped[datetime | None] = Column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = Column(DateTime, nullable=True)

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------

    # Many Tasks belong to one User
    owner = relationship("UserModel", back_populates="tasks")

    # Many Tasks belong to one Job (Optional)
    job = relationship("JobModel", back_populates="tasks")

    # Note: We need to define 'tasks' relationship on JobModel as well.

    def __repr__(self):
        return f"<TaskModel(id='{self.id}', title='{self.title}', status='{self.status}')>"
