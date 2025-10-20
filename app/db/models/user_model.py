import uuid
from datetime import datetime, UTC
from typing import Optional, List, TYPE_CHECKING

# The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy import Text, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Use UUID from postgresql dialects for best performance
from sqlalchemy.dialects.postgresql import UUID

# CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base 

# Type Checking for Relationships
if TYPE_CHECKING:
    # IMPORTANT: These imports are only for static type checkers (like Mypy)
    from app.db.models.artifact_model import Artifact
    from app.db.models.job_model import Job # Assuming a Job model exists


# =========================================================================
# 🛡️ CORE ORM MODEL: User
# =========================================================================
class User(Base):
    """
    Represents a user or system client, linked to Keycloak. 
    The core identity entity for all transactional data.
    """
    __tablename__ = "users"
    __allow_unmapped__ = False 

    # 🥇 Primary Key (UUID) - Internal ID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Internal UUID for the user record.",
    )
    
    # 🔑 Keycloak Linkage - The immutable ID from the Identity Provider
    keycloak_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
        doc="The UUID assigned to the user by Keycloak.",
    )
    
    # --- Identification ---

    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False,
        doc="User's primary email address (used for login)."
    )

    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="User's full name, as provided by the IDP."
    )

    # --- Permissions and Status ---

    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        doc="Whether the user account is active."
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        doc="Whether the user has full administrative rights."
    )

    # --- Timestamps ---

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the user record was first created.",
    )

    # --- Relationships ---
    
    # One-to-Many: Artifacts created/owned by this user
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="All transactional artifacts owned by this user."
    )
    
    # One-to-Many: Jobs owned by this user
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="owner",
        cascade="all, delete-orphan",
        doc="All jobs or job definitions owned by this user."
    )
    
    def __repr__(self) -> str:
        """A simple, informative representation for logging and debugging."""
        return (
            f"<User(email='{self.email}', kc_id='{self.keycloak_id}', "
            f"superuser={self.is_superuser})>"
        )
