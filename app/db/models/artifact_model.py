import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, TYPE_CHECKING

# 💥 The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy import ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Use JSONB and UUID from postgresql dialects for best performance if using Postgres
from sqlalchemy.dialects.postgresql import UUID, JSONB

# 🔑 CRITICAL: Import the Base class from the database configuration!
from app.db.database import Base


# 🔗 Type Checking for Relationships
if TYPE_CHECKING:
    from app.db.models.job_model import Job


# =========================================================================
# 🛡️ Enums for types of Input documents
# =========================================================================
class ArtifactType(str, enum.Enum):
    """Types of files or data linked to a job."""

    CONTEXT = "context"
    CONTENT = "content"
    OUTPUT_SCHEMA = "output"
    TEMPLATE = "template"


# =========================================================================
# 🛡️ CORE ORM MODELS
# =========================================================================
class Artifact(Base):
    """Data input/output associated with a Job. The receipts of Chuck's work."""

    __tablename__ = "artifacts"
    __allow_unmapped__ = False

    # Primary Key using Mapped style
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique UUID for the artifact.",
    )

    # Foreign Key to the Job table
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.job_id", ondelete="CASCADE"), doc="The UUID of the parent job."
    )

    # Enum for type safety
    type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType),
        nullable=False,
        doc="The type of artifact (input, output, context, etc.).",
    )

    # Text for file paths that might be longer than standard String
    file_path: Mapped[str] = mapped_column(
        Text, nullable=False, doc="MinIO path or filename."
    )

    # ⚠️ CRITICAL: Must rename column to 'metadata_' in Python because 'metadata' is reserved.
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        name="metadata",  # Use name='metadata' to map back to the DB column
        doc="Arbitrary JSON metadata about the artifact.",
    )

    # Timestamp with timezone support
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the artifact was created/uploaded.",
    )

    # --- Relationships ---
    job: Mapped["Job"] = relationship(
        back_populates="artifacts", doc="The parent job that owns this artifact."
    )

    def __repr__(self) -> str:
        return f"<Artifact(id='{self.id}', type='{self.type.value}', job_id='{self.job_id}')>"
