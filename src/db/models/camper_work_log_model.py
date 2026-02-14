# File: src/db/models/camper_work_log_model.py
"""
CamperWorkLogModel - Append-only work log for service jobs.
Tracks work sessions, wait starts, and wait ends.

No editing, no deleting. Nino gets an honest audit trail.

"We spend 40% of job time waiting for parts" -> fix the supply chain.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Float, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class LogType(str, enum.Enum):
    """What kind of log entry"""
    WORK = "work"
    WAIT_START = "wait_start"
    WAIT_END = "wait_end"


class CamperWorkLogModel(Base):
    """
    An append-only log entry for a service job.
    WORK = mechanic logged hours. WAIT_START/WAIT_END = waiting period tracking.
    """
    __tablename__ = 'camper_work_logs'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Which job
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_service_jobs.id'),
        nullable=False,
        index=True
    )

    # Which bay (optional -- some work happens outside a bay)
    bay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_bays.id'),
        nullable=True
    )

    # Log type
    log_type: Mapped[LogType] = mapped_column(
        SQLEnum(LogType, name='camper_log_type', create_constraint=True),
        nullable=False
    )

    # Work hours (only for WORK entries)
    hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Hours worked (only for WORK type)"
    )

    # What was done / why waiting
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What was done or why waiting"
    )

    # Wait reason (only for WAIT_START)
    wait_reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="e.g., 'Glue curing', 'Parts on order', 'Paint drying'"
    )

    # Who logged it
    logged_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Username from token"
    )

    # When
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    job: Mapped["CamperServiceJobModel"] = relationship(back_populates="work_logs")
    bay: Mapped["CamperBayModel"] = relationship()

    def __repr__(self):
        return f"<CamperWorkLog(job_id={self.job_id}, type={self.log_type}, hours={self.hours})>"
