# File: app/db/models/user_model.py
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column 
from sqlalchemy import String, DateTime, Boolean, JSON, UniqueConstraint

from app.db.models.artifact_model import ArtifactModel
from app.db.models.job_model import JobModel
from app.db.models.message_tasks_model import MessageTaskModel
from app.db.models.pipeline_tasks_model import PipelineTaskModel
from app.db.models.refresh_token_model import RefreshTokenModel
from app.db.models.task_model import TaskModel
from .base import Base

class UserModel(Base):
    __tablename__ = 'users'

    # Primary Key (Use mapped_column to apply arguments)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, comment="The UUID from the Identity Provider (Keycloak)")

    # Core Identity Fields
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Application State and Metadata
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="Flag indicating if the user has completed application onboarding")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # User Preferences and Custom Data
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="Arbitrary JSON field for user-specific settings (e.g., theme, layout)")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (Adding 'initializer' to complete the back_populates from InitializerModel)
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    jobs: Mapped[list["JobModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    tasks: Mapped[list["TaskModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    artifacts: Mapped[list["ArtifactModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    
    # 💥 CRITICAL FIX: Rename to 'initiated_message_tasks' to satisfy MessageTaskModel's back_populates
    initiated_message_tasks: Mapped[list["MessageTaskModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    
    pipeline_tasks: Mapped[list["PipelineTaskModel"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    # New relationship to complete the InitializerModel's back_populates
    initializer: Mapped["InitializerModel"] = relationship(back_populates="admin_user")

    def __repr__(self):
        return f"<UserModel(id='{self.id}', username='{self.username}', email='{self.email}')>"
