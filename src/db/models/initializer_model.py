# File: app/db/models/initializer_model.py - FINAL FIX
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.models.pipeline_tasks_model import PipelineTaskModel # Ensure mapped_column is imported
from .base import Base

class InitializerModel(Base):
    __tablename__ = 'initializer'
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Status Flags
    keycloak_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_user_created: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    storage_buckets_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Foreign key to the initial admin user created
    admin_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ----------------------------------------------------
    # Relationships
    # ----------------------------------------------------
   
    # Relationship to the Admin User (One Initializer record belongs to one Admin User)
    admin_user: Mapped["UserModel"] = relationship(
        "UserModel", 
        back_populates="initializer",
        foreign_keys=[admin_user_id] # Explicitly define the FK
    )

    # 💥 CRITICAL FIX: Add the missing 'pipeline_tasks' property (One Initializer -> Many PipelineTasks)
    pipeline_tasks: Mapped[list["PipelineTaskModel"]] = relationship(
        back_populates="initializer",
        cascade="all, delete-orphan" # If the initializer record is deleted, related tasks should go too
    )

    def __repr__(self):
        return f"<InitializerModel(id='{self.id}', keycloak_ready={self.keycloak_ready})>"