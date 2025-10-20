import enum
import uuid
from datetime import datetime, UTC
from typing import Optional, Dict, Any, TYPE_CHECKING

# The Powerhouse Imports: SQLAlchemy 2.0 Style
from sqlalchemy import ForeignKey, Enum, Text, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Note: Use JSONB and UUID from postgresql dialects for best performance
from sqlalchemy.dialects.postgresql import UUID, JSONB

# CRITICAL: Import the Base class from the database configuration!
from app.db.models.base import Base 

# Type Checking for Relationships
if TYPE_CHECKING:
    from app.db.models.artifact_model import Artifact

# =========================================================================
# 🛡️ Enums for Task Status
# =========================================================================
class TaskStatus(str, enum.Enum):
    """The status of a single execution step (task)."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    RETRY_SCHEDULED = "retry_scheduled"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =========================================================================
# 🛡️ CORE ORM MODEL: MessageTask
# =========================================================================
class MessageTask(Base):
    """
    Represents a specific execution step (task) performed on a single Artifact. 
    Used for granular EOIO, history, and retry tracking.
    """
    __tablename__ = "message_tasks"
    __allow_unmapped__ = False 

    # 🥇 Primary Key (UUID)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique UUID for the task execution record.",
    )
    
    # 🔗 Foreign Key: Artifact
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), 
        index=True,
        doc="The UUID of the Artifact being processed.",
    )
    
    # --- Execution Definition ---
    
    task_name: Mapped[str] = mapped_column(
        String(128), 
        nullable=False,
        doc="The specific worker function or logical task executed (e.g., 'Transform_A_to_B')."
    )

    execution_order: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        doc="Sequential order of this task within the defined pipeline."
    )
    
    # --- State and Retry Management ---

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
        doc="Status of this task execution (PENDING, SUCCESS, FAILED).",
    )
    
    retry_count: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        doc="Number of times this specific task has been attempted for this artifact."
    )

    # --- Diagnostics ---
    
    # Raw traceback or detailed error message
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Raw system traceback or detailed error message on failure."
    )

    # CRITICAL: Structured JSON analysis provided by the LLM on failure
    llm_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Structured, actionable diagnosis provided by the LLM (e.g., suggested fix, root cause)."
    )

    # --- Timestamps ---
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(UTC),
        doc="When the task execution record was created.",
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the task worker started execution."
    )
    
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the task worker completed execution (success or fail)."
    )
    
    # --- Relationships ---
    
    # Many-to-One: The Artifact this task is operating on
    artifact: Mapped["Artifact"] = relationship(
        "Artifact",
        back_populates="tasks",
        doc="The parent artifact being processed."
    )

    def __repr__(self) -> str:
        """A simple, informative representation for logging and debugging."""
        return (
            f"<MessageTask(id='{self.id}', artifact='{self.artifact_id}', "
            f"name='{self.task_name}', status='{self.status.value}')>"
        )
