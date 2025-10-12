import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, UTC # ✅ Consistent UTC import

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base # ✅ Consistent Base import

# --- Type Checking Imports ---
if TYPE_CHECKING:
    from .user_model import User


# =========================================================================
# 🛡️ TEAM ORM MODEL
# =========================================================================
class Team(Base):
    """
    Represents a user team or organization.
    Converted entirely to modern SQLAlchemy 2.0 Mapped style.
    """

    __tablename__ = "teams"
    __allow_unmapped__ = False # Added for consistency

    # 🔑 Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4, # ✅ Using Python default for consistency
        doc="Unique UUID for the Team/Organization.",
    )

    # 📛 Team Name
    name: Mapped[str] = mapped_column(
        String(255), unique=True, doc="The unique name of the team."
    )

    # ⏰ Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC), # ✅ Consistent UTC
        doc="Time the team record was created.",
    )

    updated_at: Mapped[datetime] = mapped_column( # Changed Optional to Required with onupdate
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC), # ✅ Consistent UTC
        doc="Last time the team record was updated.",
    )

    # 🤝 Relationships (One-to-Many: One Team has Many Users)
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="team",
        cascade="all, delete-orphan", 
        doc="List of all users belonging to this team.",
    )

    def __repr__(self):
        return f"<Team(id='{self.id}', name='{self.name}')>"
