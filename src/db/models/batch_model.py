# File: src/db/models/batch_model.py
"""
BatchModel - A batch from Molly's kitchen.
What she made today. 20 salads at 4AM. Tracked from farm to belly.

"20 salads today. The lettuce... I got to pick." - Molly
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, time, timezone
from sqlalchemy import String, DateTime, Date, Time, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class FreshnessRule(str, enum.Enum):
    """No day-olds. Super fresh."""
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    THREE_DAY = "three_day"
    WEEK = "week"
    MONTH = "month"


class BatchStatus(str, enum.Enum):
    """Where is this batch in the lifecycle?"""
    CREATED = "created"
    PENDING_TEST = "pending_test"
    TESTING = "testing"
    APPROVED = "approved"
    REJECTED = "rejected"
    RESCUED = "rescued"          # Pink Punch saved it!
    IN_DISTRIBUTION = "in_distribution"
    DISTRIBUTED = "distributed"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class BatchModel(Base):
    """
    A batch of products from a farm/kitchen.
    All items in a batch share the same origin and test results.
    """
    __tablename__ = 'batches'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Batch Identity
    batch_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique batch code (e.g., MOL-2025-1211-001)"
    )
    batch_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable batch name"
    )

    # What
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of items (salad, dressing, cheese, etc.)"
    )
    recipe_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Recipe used (e.g., Molly's Simple Salad)"
    )

    # Origin
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('farms.id'),
        nullable=True
    )
    production_location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Where it was made (e.g., Molly's Kitchen)"
    )

    # When
    production_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    production_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        comment="Time production started (e.g., 04:00)"
    )
    made_by: Mapped[str] = mapped_column(
        String(100),
        default="Unknown",
        nullable=False,
        comment="Who made this batch (e.g., Molly)"
    )

    # Quantity
    quantity_made: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total items produced"
    )
    quantity_unit: Mapped[str] = mapped_column(
        String(20),
        default="portion",
        nullable=False
    )
    quantity_remaining: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Items still available"
    )

    # Freshness
    freshness_rule: Mapped[FreshnessRule] = mapped_column(
        SQLEnum(FreshnessRule),
        default=FreshnessRule.SAME_DAY,
        nullable=False
    )
    shelf_life_hours: Mapped[int] = mapped_column(
        Integer,
        default=24,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Status
    status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus),
        default=BatchStatus.CREATED,
        nullable=False
    )

    # Lab Testing (lab_test_id removed - use lab_tests relationship instead)
    # LabTestModel has batch_id FK pointing here
    lab_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    lab_certificate: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Certificate code from Felix"
    )

    # Quality
    quality_grade: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        comment="A+, A, B, C, D, F"
    )
    quality_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    is_good_batch: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="17/20 are good, 3/20 need Pink Punch"
    )

    # Pink Punch Rescue
    was_rescued: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bad batch saved with Pink Punch"
    )
    rescue_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="How it was saved (e.g., '5 drops Pink Punch, spinach salad')"
    )

    # Ingredients (for full traceability)
    ingredient_batches: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated batch codes of ingredients"
    )

    # Stats
    items_sold: Mapped[int] = mapped_column(Integer, default=0)
    items_given_free: Mapped[int] = mapped_column(Integer, default=0)
    items_wasted: Mapped[int] = mapped_column(Integer, default=0)
    items_composted: Mapped[int] = mapped_column(Integer, default=0)

    # Revenue
    revenue_chf: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
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
    farm: Mapped["FarmModel"] = relationship(back_populates="batches")
    lab_tests: Mapped[list["LabTestModel"]] = relationship(back_populates="batch")
    traceable_items: Mapped[list["TraceableItemModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    trace_events: Mapped[list["TraceEventModel"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BatchModel(code='{self.batch_code}', type='{self.item_type}', qty={self.quantity_made})>"
