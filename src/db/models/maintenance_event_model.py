# File: src/db/models/maintenance_event_model.py
"""
MaintenanceEventModel - When things break, COOLIE gets the parts.
Scheduled maintenance, emergency repairs, the works.

"I can handle it. Found the part. Hard to find." - SAL about his coffee machine
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class MaintenanceType(str, enum.Enum):
    """What kind of maintenance"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    CALIBRATION = "calibration"
    CLEANING = "cleaning"
    UPGRADE = "upgrade"


class MaintenanceStatus(str, enum.Enum):
    """Maintenance status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceEventModel(Base):
    """
    A maintenance event on equipment.
    When things break, COOLIE gets the parts.
    """
    __tablename__ = 'maintenance_events'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What equipment
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('equipment.id'),
        nullable=False,
        index=True
    )
    equipment_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Denormalized for display"
    )

    # Type
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType),
        nullable=False
    )

    # Description
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Who
    performed_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Who did the work (e.g., Marco)"
    )

    # When
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Status
    status: Mapped[MaintenanceStatus] = mapped_column(
        SQLEnum(MaintenanceStatus),
        default=MaintenanceStatus.SCHEDULED,
        nullable=False
    )

    # Parts used
    parts_used: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated parts list"
    )
    parts_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    # Labor
    labor_hours: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )
    labor_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )

    # Total
    total_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="CHF",
        nullable=False
    )

    # Result
    issue_found: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Fixed, Needs parts, Replaced, etc."
    )

    # Downtime
    downtime_hours: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    # Follow-up
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_maintenance_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Parts ordered
    waiting_for_parts: Mapped[bool] = mapped_column(Boolean, default=False)
    parts_order_po: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="PO number for parts"
    )

    # Photos
    before_photos: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated URLs"
    )
    after_photos: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    equipment: Mapped["EquipmentModel"] = relationship(back_populates="maintenance_events")

    def __repr__(self):
        return f"<MaintenanceEventModel(equipment='{self.equipment_name}', type={self.maintenance_type}, status={self.status})>"
