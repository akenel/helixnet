import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, TYPE_CHECKING

# The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy import ForeignKey, Enum, Text, DateTime, String, Integer, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Use JSONB and UUID from postgresql dialects for best performance
from sqlalchemy.dialects.postgresql import UUID, JSONB

# CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base 

# Type Checking for Relationships
if TYPE_CHECKING:
    from app.db.models.user_model import User
    from app.db.models.message_task_model import MessageTask

# =========================================================================
# 🛡️ Enums for Artifact Status and Type
# =========================================================================
class ArtifactType(str, enum.Enum):
    """Defines the structural type of the artifact."""
    INPUT_PAYLOAD = "input_payload"
    OUTPUT_PAYLOAD = "output_payload"
    CONTROL_FILE = "control_file"
    LOG = "log"
    DIAGNOSTICS = "diagnostics"

class ArtifactStatus(str, enum.Enum):
    """The current processing status of the transactional document."""
    RECEIVED = "received"
    VALIDATING = "validating"
    QUEUED_FOR_EOIO = "queued_for_eoio"
    TRANSFORMING = "transforming"
    DELIVERED = "delivered"
    VALIDATION_FAILED = "validation_failed"
    DELIVERY_FAILED = "delivery_failed"
    PERMANENTLY_FAILED = "permanently_failed"


# =========================================================================
# 🛡️ CORE ORM MODEL: Artifact
# =========================================================================
class Artifact(Base):
    """
    Represents a single message or payload (e.g., a file, an IDOC) 
    that moves through the HelixNet pipeline. This is the root transactional 
    document.
    """
    __tablename__ = "artifacts"
    __allow_unmapped__ = False 

    # 🥇 Primary Key (UUID)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique UUID for the artifact.",
    )
    
    # 🔗 Foreign Key: User (Owner/Creator - Assuming all artifacts have an origin user)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True,
        doc="The UUID of the user/system who owns this artifact.",
    )

    # --- Data Definition Fields ---

    interface_name: Mapped[str] = mapped_column(
        String(128), 
        index=True, 
        nullable=False,
        doc="A logical name for the interface (e.g., 'BankFile_Inbound_V23')."
    )

    type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType),
        nullable=False,
        default=ArtifactType.INPUT_PAYLOAD,
        doc="The artifact's structural type (input, output, control file, etc.).",
    )
    
    # --- EOIO and State Management ---
    
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus),
        nullable=False,
        default=ArtifactStatus.RECEIVED,
        index=True,
        doc="Current processing status (e.g., RECEIVED, DELIVERED, FAILED).",
    )
    
    sequence_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        index=True,
        doc="Required for EOIO: Sequential order within its interface/sender group."
    )

    is_permanently_failed: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        doc="Flag for the Dashboard to indicate a permanent failure requiring manual attention."
    )

    # --- MinIO & File Attributes ---

    minio_key: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="MinIO path or S3 key for the raw data blob."
    )
    
    size_bytes: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True, 
        doc="The size of the artifact file in bytes."
    )

    # --- Version Control and Audit Trail (The Immutable Links) ---

    mapping_config_vid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        nullable=False, 
        doc="REQUIRED GUID: Which version of the mapping code was used."
    ) 

    control_file_vid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        nullable=False, 
        doc="REQUIRED GUID: Which version of the external lookup files were used."
    ) 

    pipeline_vid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        nullable=False, 
        doc="REQUIRED GUID: Which pipeline definition (sequence of tasks) was executed."
    )
    
    # --- Timestamps & Metadata ---

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the artifact was created/received.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
        doc="Last time the status was updated.",
    )
    
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        name="metadata", 
        doc="Arbitrary JSON metadata, source system IDs, etc.",
    )

    # --- Relationships ---
    
    # One-to-Many: All tasks executed against this artifact
    tasks: Mapped[list["MessageTask"]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
        doc="List of all execution steps for this artifact."
    )
    
    # One-to-One: The User who owns this artifact (assuming User model exists)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="artifacts", 
        lazy="joined", 
        doc="The user object linked to this artifact."
    )
    
    def __repr__(self) -> str:
        """A simple, informative representation for logging and debugging."""
        return (
            f"<Artifact(id='{self.id}', interface='{self.interface_name}', "
            f"seq='{self.sequence_number}', status='{self.status.value}')>"
        )
