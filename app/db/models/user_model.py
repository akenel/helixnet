import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, UTC # ✅ Consistent UTC import

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY # 🎯 ADDED ARRAY IMPORT

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base # ✅ Consistent Base import

# --- Type Checking Imports ---
if TYPE_CHECKING:
    from .team_model import Team 
    from .job_model import Job, TaskResult
    from .artifact_model import Artifact
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

    # 📛 User Name 
    username: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        doc="User's unique human-readable username for identification.",
    )

    # 📛 Full Name 
    fullname: Mapped[str] = mapped_column(
        String(100), 
        index=True, 
        doc="User's fullname ",
    )

    # 🔒 Security
    hashed_password: Mapped[str] = mapped_column(
        Text, doc="The securely hashed password."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, doc="If the account is active and usable."
    )

    is_admin: Mapped[bool] = mapped_column(
        "is_admin", 
        Boolean, 
        default=False, 
        doc="If the user has administrative privileges (mapped to 'is_admin' column in DB).",
    )
    
    # 🎯 NEW CRITICAL FIELDS: Scopes and Roles for Authentication!
    # These map directly to the JWT claims and authentication logic.
    scopes: Mapped[List[str]] = mapped_column(
        ARRAY(String), 
        default=["user"], 
        doc="List of application scopes/permissions the user possesses."
    )
    roles: Mapped[List[str]] = mapped_column(
        ARRAY(String), 
        default=["basic"], 
        doc="List of abstract roles the user belongs to (e.g., 'admin', 'editor', 'basic')."
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
    
    # 💼 Jobs Relationship 
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="user", 
        doc="The list of asynchronous jobs or tasks created or owned by this user.",
    )

    # 🎯 Task Results Relationship 
    task_results: Mapped[List["TaskResult"]] = relationship(
        "TaskResult",
        back_populates="user", 
        doc="The list of results from background tasks (Celery/Job results) associated with this user.",
    )
    
    # 🖼️ Artifacts Relationship 
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="user", 
        doc="The list of all artifacts (e.g., reports, files, project docs) created or owned by this user.",
    )
    
    # 🔑 Refresh Tokens Relationship 
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
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
