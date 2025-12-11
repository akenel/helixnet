# File: src/db/models/lab_test_model.py
"""
LabTestModel - Felix tests every batch.
The stamp of approval. The certificate. The Pink Punch rescue.

"I take it back to the lab." - SAL about Molly's bad batches
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class LabTestStatus(str, enum.Enum):
    """Lab test status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    RESCUED = "rescued"      # Pink Punch save!


class QualityGrade(str, enum.Enum):
    """Quality assessment"""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class LabTestModel(Base):
    """
    Felix tests Molly's batch.
    Every batch gets tested. No exceptions.
    Bad batch? Pink Punch it!
    """
    __tablename__ = 'lab_tests'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What batch
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('batches.id'),
        nullable=False,
        index=True
    )
    batch_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Denormalized for quick lookup"
    )

    # Who tested
    tested_by: Mapped[str] = mapped_column(
        String(100),
        default="Felix",
        nullable=False
    )
    lab_name: Mapped[str] = mapped_column(
        String(100),
        default="Felix Lab",
        nullable=False
    )

    # When
    tested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Tests performed
    contamination_check: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="No dirt, bugs, foreign matter"
    )
    contamination_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    freshness_check: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    freshness_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    temperature_check: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Cold chain maintained"
    )
    temperature_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    temperature_reading: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="e.g., '4.2C'"
    )

    visual_check: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    visual_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    taste_test: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    taste_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Results
    all_passed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    status: Mapped[LabTestStatus] = mapped_column(
        SQLEnum(LabTestStatus),
        default=LabTestStatus.PENDING,
        nullable=False
    )
    quality_grade: Mapped[QualityGrade | None] = mapped_column(
        SQLEnum(QualityGrade),
        nullable=True
    )

    # Failure details
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why it failed"
    )

    # Rescue (Pink Punch)
    can_be_rescued: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bad batch can be saved?"
    )
    rescue_method: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="How to save it (e.g., '5 drops Pink Punch')"
    )
    was_rescued: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    rescued_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    rescued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Certificate
    certificate_code: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        comment="e.g., FELIX-MOL-2025-001"
    )
    certificate_issued: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    certificate_expires: Mapped[datetime | None] = mapped_column(
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

    # Relationships
    batch: Mapped["BatchModel"] = relationship(back_populates="lab_tests")

    def __repr__(self):
        return f"<LabTestModel(batch='{self.batch_code}', status={self.status}, grade={self.quality_grade})>"
