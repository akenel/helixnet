import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.database import Base

# --- Type Checking Imports ---
if TYPE_CHECKING:
    # We only need the User model here because of the 'users' relationship
    from app.db.models.user_model import User


# =========================================================================
# 🛡️ TEAM ORM MODEL
# =========================================================================
class Team(Base):
    """
    Represents a user team or organization.
    Converted entirely to modern SQLAlchemy 2.0 Mapped style.
    """

    __tablename__ = "teams"
    __allow_unmapped__ = False

    # 🔑 Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=func.uuid_generate_v4(),
        doc="Unique UUID for the Team/Organization.",
    )

    # 📛 Team Name
    name: Mapped[str] = mapped_column(
        String(255), unique=True, doc="The unique name of the team."
    )

    # ⏰ Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        doc="Time the team record was created.",
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        doc="Last time the team record was updated.",
    )

    # 🤝 Relationships (One-to-Many: One Team has Many Users)
    # Note: The User model must contain a 'team_id' foreign key for this to work.
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="team",
        cascade="all, delete-orphan",  # Deleting a team deletes all linked users (if allowed by business logic)
        doc="List of all users belonging to this team.",
    )

    def __repr__(self):
        return f"<Team(id='{self.id}', name='{self.name}')>"
