# File: app/db/models/artifact_model.py
import enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
# Import mapped_column and Mapped to use the 2.0 style
from sqlalchemy import String, DateTime, Text, BigInteger, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base
class ArtifactType(enum.Enum):
    """Defines the category of data the artifact represents."""
    RAW = "raw"             # Raw data, untouched
    PROCESSED = "processed" # Output from a processing step
    REPORT = "report"       # Human-readable document/summary
    MODEL = "model"         # ML model artifact (e.g., serialized weights)
    CONTEXT = "context"
    CONTENT = "content"
    SCHEMA  = "schema"
    J2="j2"
    TONE  = "tone"
    AI_PROMPT = "ai_prompt"
    CUSTOM="CustomArtifactType"

class ArtifactModel(Base):
    __tablename__ = 'artifacts'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
   # Core Metadata (mapped_column fixes applied)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Human-readable filename or title")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), default=ArtifactType.RAW, nullable=False)
    
    # Storage and Size (mapped_column fixes applied)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True, comment="The object key/path in the external storage (MinIO)")
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    # Ownership and Lineage (mapped_column fixes applied)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    # This foreign key references the JobModel:
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    pipeline_task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('pipeline_tasks.id'), nullable=False) 
 
    # The relationship property (must be singular)
    pipeline_task: Mapped["PipelineTaskModel"] = relationship(
        back_populates="artifacts", # Matches the new plural name on PipelineTaskModel
        foreign_keys=[pipeline_task_id]
    )
    # Optional Custom Metadata (mapped_column fixes applied)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="Arbitrary JSON metadata about the artifact")

    # Timestamps (mapped_column fixes applied)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------
    owner: Mapped["UserModel"] = relationship(back_populates="artifacts") 
    job: Mapped["JobModel"] = relationship(back_populates="artifacts", foreign_keys=[job_id])
    pipeline_task: Mapped["PipelineTaskModel"] = relationship(back_populates="artifacts", foreign_keys=[pipeline_task_id])
 
    def __repr__(self):
        return f"<ArtifactModel(id='{self.id}', name='{self.name}', key='{self.storage_key}')>"
    