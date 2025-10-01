"""
SQLAlchemy Models Package
Import from app.db.models.user and app.db.models.job_result instead.
"""
# NEW - Must import datetime and UTC
from datetime import datetime, UTC
from pydoc import text
from typing import Optional
import uuid
from app.db.database import Base
from app.db.models.user import User
from app.db.models.job_result import JobResult
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any
from sqlalchemy import text

__all__ = ['User', 'JobResult']

class JobResult(Base):
    """Stores results and status of background Celery tasks."""
    __tablename__ = "job_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )
    task_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING"
    )
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(UTC) # Correct: Uses timezone-aware UTC now
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True
    )

    # Relationship to User
    user: Mapped["User"] = relationship(back_populates="job_results")
# --- 3. Job Result Model ---
    def __repr__(self) -> str:
        return f"<JobResult(id='{self.id}', task_id='{self.task_id}', status='{self.status}')>"
    
class User(Base):
    """User model for authentication and user management."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=text("true")
    )
    is_superuser: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(UTC) # Correct: Uses timezone-aware UTC now
    )

    # Relationship to JobResult
    job_results: Mapped[list["JobResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"
# The above code is a refactored version of the original task_model.py
# It combines both User and JobResult models into a single file for better organization.
# It also ensures that datetime fields are timezone-aware by using UTC. 