import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, TYPE_CHECKING

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy import ForeignKey, Enum, Text, DateTime, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Use JSONB and UUID from postgresql dialects for best performance if using Postgres
from sqlalchemy.dialects.postgresql import UUID, JSONB

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base # <--- MANDATORY INHERITANCE IMPORT << CN-OOP

# 🔗 Type Checking for Relationships
if TYPE_CHECKING:
    # IMPORTANT: These imports are only for static type checkers (like Mypy)
    # and prevent circular import issues at runtime.
    from app.db.models.job_model import Job
    from app.db.models.user_model import User


# =========================================================================
# 🛡️ Enums for types of Input documents
# =========================================================================
class ArtifactType(str, enum.Enum):
    """Types of files or data linked to a job. Defining the artifact's purpose."""

    CONTEXT = "context"
    CONTENT = "content"
    OUTPUT_SCHEMA = "output"
    TEMPLATE = "template"
    # New types for flexibility
    RESULT = "result"
    LOG = "log"


# =========================================================================
# 🛡️ CORE ORM MODEL: Artifact
# =========================================================================
class Artifact(Base):
    """
    Data input/output associated with a Job. 
    The raw materials and final receipts of Chuck's work.
    """

    __tablename__ = "artifacts"
    __allow_unmapped__ = False # Enforce Mapped style

    # 🥇 Primary Key (UUID)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique UUID for the artifact.",
    )
    
    # 🔗 Foreign Key: User (Owner)
    # CRITICAL FIX: Defines the foreign key linking the artifact to its creator.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True,
        doc="The UUID of the user who owns/uploaded this artifact.",
    )

    # 🔗 Foreign Key: Job (Context)
    # FIX: Corrected reference from "jobs.id" to the actual PK in the Job model, "jobs.job_id".
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="SET NULL"), 
        nullable=True,
        index=True,
        doc="The UUID of the parent job, if this artifact is job-related.",
    )
    
    # --- Data Definition Fields ---

    type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType),
        nullable=False,
        doc="The artifact's purpose (input, output, context, etc.).",
    )

    file_path: Mapped[str] = mapped_column(
        Text, 
        nullable=False, 
        doc="MinIO path or S3 key (the definitive storage location)."
    )

    # Optional Fields from the old structure, converted to Mapped style
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True, 
        doc="The file's MIME type (e.g., 'application/json')."
    )

    size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True, 
        doc="The size of the artifact file in bytes."
    )
    
    # ⚠️ CRITICAL: Must rename column to 'metadata_' in Python because 'metadata' is reserved.
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        name="metadata",  # Use name='metadata' to map back to the DB column
        doc="Arbitrary JSON metadata about the artifact.",
    )

    # --- Timestamps ---

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the artifact was created/uploaded.",
    )

    # --- Relationships ---
    
    # Many-to-One: The User who owns this artifact
    user: Mapped["User"] = relationship(
        "User",
        back_populates="artifacts", 
        lazy="joined", # Fetch user details when fetching artifact
        doc="The user object linked to this artifact."
    )

    # Many-to-One: The Job this artifact belongs to (can be null)
    job: Mapped[Optional["Job"]] = relationship(
        back_populates="artifacts", 
        doc="The parent job object this artifact is related to."
    )

    
    def __repr__(self) -> str:
        """A simple, informative representation for logging and debugging."""
        return (
            f"<Artifact(id='{self.id}', type='{self.type.value}', "
            f"owner='{self.user_id}', job='{self.job_id}')>"
        )
