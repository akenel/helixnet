# File: src/db/models/trace_event_model.py
"""
TraceEventModel - Every touch point in the chain.
The audit trail. The SPINE. Every time something happens to an item.

Who. What. When. Where. Why.
TAXMAN HAPPY.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base
from .traceable_item_model import LifecycleStage, LocationType


class ActorType(str, enum.Enum):
    """Who touched it - The Cast"""
    # Farm & Production
    FARMER = "farmer"              # MOLLY, Brothers
    PROCESSOR = "processor"        # Kitchen staff
    LAB_TECH = "lab_tech"          # FELIX and team

    # Logistics & Freight (YUKI's domain)
    FREIGHT_COORDINATOR = "freight_coordinator"  # YUKI - The Boss
    FREIGHT_SECURITY = "freight_security"        # CHARLIE - Eyes & Ears
    PORT_AUTHORITY = "port_authority"            # HANK - The Stamp
    PORT_WORKER = "port_worker"                  # DIRK - The Hands
    CUSTOMS_AGENT = "customs_agent"              # Ka-MAKI - The Papers
    DRIVER = "driver"                            # Transport

    # Equipment & Build
    EQUIPMENT_TECH = "equipment_tech"            # MARCO - The Builder
    SUPPLIER = "supplier"                        # External suppliers

    # Service & Sales
    BAR_STAFF = "bar_staff"        # SAL and team
    MACHINE = "machine"            # COOLIE, scanners
    CUSTOMER = "customer"          # End users
    SYSTEM = "system"              # Automated events


class TraceEventModel(Base):
    """
    Every time something happens to an item.
    This is the audit trail - the heart of the SPINE.
    """
    __tablename__ = 'trace_events'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What item
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('traceable_items.id'),
        nullable=False,
        index=True
    )
    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Denormalized for quick lookup"
    )

    # What batch
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('batches.id'),
        nullable=True,
        index=True
    )
    batch_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    # Event sequence
    event_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential within item"
    )

    # What happened
    stage: Mapped[LifecycleStage] = mapped_column(
        SQLEnum(LifecycleStage),
        nullable=False
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="harvested, tested, shipped, sold, etc."
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Where
    location_type: Mapped[LocationType] = mapped_column(
        SQLEnum(LocationType),
        nullable=False
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    location_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    location_address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    # Who
    actor_type: Mapped[ActorType] = mapped_column(
        SQLEnum(ActorType),
        nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    actor_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # When
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Quality check
    quality_check: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    quality_grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True
    )
    quality_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Quantity tracking
    quantity_before: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    quantity_after: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    quantity_unit: Mapped[str] = mapped_column(
        String(20),
        default="portion",
        nullable=False
    )

    # Temperature (cold chain)
    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    temperature_ok: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Evidence
    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    signature: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Digital signature for verification"
    )

    # Special flags
    is_pink_punch: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bad batch rescued"
    )
    is_lost_soul: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Given to SAL's people"
    )
    is_anomaly: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Something unexpected"
    )
    anomaly_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Device/system info
    device_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Scanner/terminal ID"
    )
    app_version: Mapped[str | None] = mapped_column(
        String(20),
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
    item: Mapped["TraceableItemModel"] = relationship(back_populates="trace_events")
    batch: Mapped["BatchModel"] = relationship(back_populates="trace_events")

    def __repr__(self):
        return f"<TraceEventModel(item='{self.item_code}', stage={self.stage}, action='{self.action}')>"
