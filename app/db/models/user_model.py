import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, TYPE_CHECKING

# 📚 SQLAlchemy Imports
from sqlalchemy import ForeignKey, Enum, JSON, Text, Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

# 🧱 Import Base from the definitive location
from app.db.database import Base # 🎯 ASSUMING Base is defined in database.py


# =========================================================================
# 💡 FORWARD REFERENCES (Fixes Circular Imports in Relationships) 💡
# =========================================================================
# Use these strings to define relationships without importing the other model files 
# at the top level, which avoids circular import issues.

if TYPE_CHECKING:
    from .job_model import Job
    # 💡 FIX 1: Change import from job_result_model to task_model
    # and change the expected class name from JobResult to TaskResult
    from .task_model import TaskResult 
    from .artifact_model import Artifact
    
    
# =========================================================================
# 🛡️ CORE ORM MODEL: USER 💾
# =========================================================================
class User(Base):
    """User Model. Chuck says: Don't mess with this table."""

    __tablename__ = "users"

    # --- Columns ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique UUID for the user.",
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC)
    )

    # --- Relationships ---
    # User owns multiple Jobs
    jobs: Mapped[List["Job"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        # Use string reference to break circular dependencies
        # This relationship assumes the Job model has a 'user' relationship
    )
    
    # User owns multiple TaskResults
    # 💡 FIX 2: Change model name reference from "JobResult" to "TaskResult"
    task_results: Mapped[List["TaskResult"]] = relationship(
        "TaskResult",
        back_populates="user",
        cascade="all, delete-orphan",
        # This relationship assumes the TaskResult model has a 'user' relationship
    )
    
    # User owns multiple Artifacts via Jobs (or directly if the Artifact model has a user_id foreign key)
    # The 'Artifact' relationship was removed here, as it's usually via Job. 
    # If you need it, ensure the Artifact model has a user_id foreign key.

    # --- Representation ---
    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}')>"
