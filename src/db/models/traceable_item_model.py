# File: src/db/models/traceable_item_model.py
"""
TraceableItemModel - THE SPINE. Any item tracked in the system.
Salad, dressing, coffee beans, goat milk - all tracked the same way.

Every gram tracked. Every person recorded. Nothing lost.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class LifecycleStage(str, enum.Enum):
    """The complete food/item lifecycle - E2E"""
    # Origin (Farm)
    SEED = "seed"
    GROW = "grow"
    HARVEST = "harvest"

    # Processing (Kitchen/Lab)
    PREP = "prep"
    TEST = "test"
    APPROVE = "approve"
    REJECT = "reject"
    PACK = "pack"

    # Distribution
    SHIP = "ship"
    DELIVER = "deliver"
    STORE = "store"
    RESTOCK = "restock"

    # Consumption
    SCAN = "scan"
    SERVE = "serve"
    EAT = "eat"

    # Feedback
    FEEDBACK = "feedback"
    RETURN = "return"
    REFILL = "refill"

    # Waste Cycle
    WASTE = "waste"
    COMPOST = "compost"
    GOAT_FEED = "goat_feed"
    SOIL = "soil"

    # Special
    PINK_PUNCH = "pink_punch"
    LOST_SOUL = "lost_soul"
    EXPIRED = "expired"


class LocationType(str, enum.Enum):
    """Where in the chain"""
    FARM = "farm"
    KITCHEN = "kitchen"
    LAB = "lab"
    WAREHOUSE = "warehouse"
    TRUCK = "truck"
    BAR = "bar"
    LOCKER = "locker"
    CAFE = "cafe"
    VENDING = "vending"
    CUSTOMER = "customer"
    COMPOST = "compost"


class TraceableItemModel(Base):
    """
    Any item in the system that needs tracking.
    This is THE SPINE - everything hangs off this.
    """
    __tablename__ = 'traceable_items'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    item_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique barcode/QR code"
    )
    item_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        comment="salad, dressing, milk, equipment, etc."
    )
    item_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    # Batch info
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('batches.id'),
        nullable=True,
        index=True
    )
    batch_code: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True
    )
    batch_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # Origin
    origin_farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('farms.id'),
        nullable=True
    )
    origin_farm_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    origin_location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Current state
    current_stage: Mapped[LifecycleStage] = mapped_column(
        SQLEnum(LifecycleStage),
        default=LifecycleStage.SEED,
        nullable=False
    )
    current_location_type: Mapped[LocationType] = mapped_column(
        SQLEnum(LocationType),
        default=LocationType.FARM,
        nullable=False
    )
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    current_location_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Current holder
    current_holder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    current_holder_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Quality
    quality_grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="A+, A, B, C, D, F"
    )
    lab_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    lab_certificate: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Freshness
    made_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    freshness_hours: Mapped[int] = mapped_column(
        Integer,
        default=24,
        nullable=False
    )

    # Temperature tracking (cold chain)
    last_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    temperature_ok: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Status flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_consumed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    is_wasted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    is_composted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Special flags
    is_pink_punch: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Rescued bad batch"
    )
    is_lost_soul: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Given to SAL's people"
    )

    # Event count
    events_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    last_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    batch: Mapped["BatchModel"] = relationship(back_populates="traceable_items")
    origin_farm: Mapped["FarmModel"] = relationship(
        back_populates="traceable_items",
        foreign_keys=[origin_farm_id]
    )
    trace_events: Mapped[list["TraceEventModel"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TraceableItemModel(code='{self.item_code}', type='{self.item_type}', stage={self.current_stage})>"
