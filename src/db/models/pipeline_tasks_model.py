# File: app/db/models/pipeline_tasks_model.py - FINAL FIX
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.models.artifact_model import ArtifactModel
from src.db.models.job_model import JobModel

from .base import Base

class PipelineTaskModel(Base):
    __tablename__ = 'pipeline_tasks'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
 
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    initializer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('initializer.id'), nullable=False) 
    
    # ... (Other mapped_columns assumed correct)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------
    
    # 💥 CRITICAL FIX: Rename 'user' to 'owner' to satisfy back_populates="owner" in UserModel.
    owner: Mapped["UserModel"] = relationship(
        back_populates="pipeline_tasks",
        foreign_keys=[user_id] # Explicitly define the FK for clarity
    )
    
    # CRITICAL FIX 1: Change to plural 'artifacts' to fix the error.
    artifacts: Mapped[list["ArtifactModel"]] = relationship(
        back_populates="pipeline_task", 
        cascade="all, delete-orphan"
    ) 
    
    initializer: Mapped["InitializerModel"] = relationship(back_populates="pipeline_tasks", foreign_keys=[initializer_id])
    
    # CRITICAL FIX 2: Check the 'jobs' relationship. 
    jobs: Mapped[list["JobModel"]] = relationship(back_populates="pipeline_task_instance", cascade="all, delete-orphan") 
    
    def __repr__(self):
        return f"<PipelineTaskModel(id='{self.id}', task_name='{self.task_name}', status='{self.status}')>"