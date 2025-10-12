import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, UTC # ✅ Consistent UTC import

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base # ✅ Consistent Base import

# --- Type Checking Imports ---
# NOTE: Make sure the file team_model.py exists in the same directory
if TYPE_CHECKING:
    from .team_model import Team 
    # 💼 NEW: Add Job model for type hints to resolve 'jobs' property error
    from .job_model import Job 
    # 🎯 NEW: Add TaskResult model for type hints to resolve 'task_results' property error
    from .task_result_model import TaskResult 
    # 🖼️ NEW: Add Artifact model for type hints to resolve 'artifacts' property error
    from .artifact_model import Artifact
    # 🔑 NEW: Add RefreshToken model for type hints to resolve 'refresh_tokens' property error
    from .refresh_token_model import RefreshToken


# =========================================================================
# 👤 USER ORM MODEL
# =========================================================================
class User(Base):
    """
    Represents a system user.
    Converted entirely to modern SQLAlchemy 2.0 Mapped style.
    """

    __tablename__ = "users"
    __allow_unmapped__ = False

    # 🔑 Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
        doc="Unique UUID for the user.",
    )

    # 📧 Email (Primary authentication identifier)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, doc="User's unique email address."
    )

    # 📛 Username (FIX for DB error/User Feature)
    # 💥 FIX: Reverting to non-nullable as requested. The seeding code will be fixed surgically.
    username: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        doc="User's unique human-readable username for identification.",
    )

    # 🔒 Security
    hashed_password: Mapped[str] = mapped_column(
        Text, doc="The securely hashed password."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, doc="If the account is active and usable."
    )
    # 💥 FIX: Keep property name 'is_admin' for service compatibility,
    # but map it to the database column 'is_superuser' (the likely name in the existing schema).
    is_admin: Mapped[bool] = mapped_column(
        "is_superuser", # <-- Database column name override
        Boolean, 
        default=False, 
        doc="If the user has administrative privileges (mapped to 'is_superuser' column in DB).",
    )

    # 🤝 Team Relationship (Foreign Key)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("teams.id"),
        nullable=True,
        doc="Foreign key pointing to the user's team ID."
    )
    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="users",
        doc="The team or organization the user belongs to (relationship object)."
    )
    
    # 💼 Jobs Relationship (FIX for missing property 'jobs' error)
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="user", 
        doc="The list of asynchronous jobs or tasks created or owned by this user.",
    )

    # 🎯 Task Results Relationship (FIX for missing property 'task_results' error)
    task_results: Mapped[List["TaskResult"]] = relationship(
        "TaskResult",
        back_populates="user", 
        doc="The list of results from background tasks (Celery/Job results) associated with this user.",
    )
    
    # 🖼️ Artifacts Relationship (FIX for missing property 'artifacts' error)
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="user", 
        doc="The list of all artifacts (e.g., reports, files, project docs) created or owned by this user.",
    )
    
    # 🔑 Refresh Tokens Relationship (NEW FIX for missing property 'refresh_tokens' error)
    # Essential for multi-session authentication and token revocation.
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user", # Assuming the RefreshToken model has a 'user' property
        doc="The list of active and pending refresh tokens issued to this user.",
    )

    # ⏰ Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="Time the user record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        doc="Last time the user record was updated.",
    )

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"
