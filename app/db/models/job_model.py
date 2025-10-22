# File: app/db/models/job_model.py - FINAL CLEANUP AND TASKS FIX
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
# Ensure we are using mapped_column and Mapped for all definitions
from sqlalchemy import String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column 
import enum

from app.db.models.artifact_model import ArtifactModel
from app.db.models.task_model import TaskModel

from .base import Base
class JobStatus(enum.Enum):
    """Defines the possible states of a Job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
class JobModel(Base):
    # The 'artifacts' relationship must use the 'job_id' column in the ArtifactModel table.
    """
    Represents a long-running, asynchronous task or a batch process
    executed by the Celery worker network.
    """
    __tablename__ = 'jobs'

    # ----------------------------------------------------
    # COLUMNS (Defined first, using mapped_column)
    # ----------------------------------------------------
    id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # NOTE: Local FK to the parent PipelineTask
    pipeline_task_fk: Mapped[uuid.UUID] = mapped_column('pipeline_task_id', UUID(as_uuid=True), ForeignKey('pipeline_tasks.id'), nullable=False)
    
    # Job Metadata/Status (Use mapped_column)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    result_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    artifact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('artifacts.id'), nullable=False)

    artifacts: Mapped[list["ArtifactModel"]] = relationship(
        back_populates="job", 
        foreign_keys="job_id", # <--- Use ONLY the column name string
        cascade="all, delete-orphan"
    )

    # Foreign Keys (LOCAL to JobModel)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # NOTE: This is the FK column linking the Job to its parent PipelineTask
    pipeline_task_fk: Mapped[uuid.UUID] = mapped_column('job_id', UUID(as_uuid=True), ForeignKey('pipeline_tasks.id'), nullable=False)
    
    # ----------------------------------------------------
    # RELATIONSHIPS
    # ----------------------------------------------------
    owner: Mapped["UserModel"] = relationship(back_populates="jobs")
    
    # One Job -> Many Artifacts (Uses string reference for FK to avoid import)
    artifacts: Mapped[list["ArtifactModel"]] = relationship(
        back_populates="job", 
        foreign_keys="ArtifactModel.job_id", 
        cascade="all, delete-orphan"
    ) 
    
    # 💥 CRITICAL FIX: Add the missing plural 'tasks' property (One Job -> Many Tasks)
    tasks: Mapped[list["TaskModel"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan"
    )

    # One Job belongs to One PipelineTask (Removed duplicate definition)
    pipeline_task_instance: Mapped["PipelineTaskModel"] = relationship(
        back_populates="jobs", 
        foreign_keys=[pipeline_task_fk]
    )

    def __repr__(self):
        return f"<JobModel(id='{self.id}', name='{self.name}', status='{self.status.value}')>"