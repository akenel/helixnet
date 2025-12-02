# File: src/db/models/payroll_run_model.py
# BLQ HR Module - Payroll Run Model
# Built for Pam, Felix, and Mosey
"""
Monthly payroll run orchestration.
One run per month. Calculates all payslips. Exports to MinIO.

Mosey Rule: Every end of day has requirements. Month-end is the big one.
"""
import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .user_model import UserModel
    from .payslip_model import PaySlipModel


class PayrollRunStatus(str, enum.Enum):
    """Status of monthly payroll run."""
    DRAFT = "draft"                 # Created, not yet calculated
    CALCULATING = "calculating"     # Calculation in progress
    PENDING_REVIEW = "pending_review"  # Calculated, awaiting manager review
    APPROVED = "approved"           # Manager approved
    PROCESSING = "processing"       # Sending payslips, exporting
    PAID = "paid"                   # Bank transfer done (manual)
    CLOSED = "closed"               # Month finalized, no more changes


class PayrollRunModel(Base):
    """
    Monthly payroll run.

    Workflow:
    1. Admin creates run (DRAFT)
    2. System calculates all payslips (CALCULATING → PENDING_REVIEW)
    3. Manager reviews and approves (APPROVED)
    4. Admin marks as paid after bank transfer (PAID)
    5. Admin closes month (CLOSED)

    MinIO exports:
    - CSV of all payslips
    - Individual PDF payslips
    - Audit log
    """
    __tablename__ = "payroll_runs"

    # ================================================================
    # Primary Key
    # ================================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # ================================================================
    # Period
    # ================================================================
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Month 1-12"
    )

    # Human-readable period name
    period_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="e.g., '2025-01' or 'Januar 2025'"
    )

    # ================================================================
    # Status & Workflow
    # ================================================================
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False
    )

    # Who created the run
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Who approved the run
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # When payments were made
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # When month was closed
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # ================================================================
    # Totals (denormalized for quick access)
    # ================================================================
    total_employees: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_hours: Mapped[str] = mapped_column(
        String(20),
        default="0.00",
        nullable=False,
        comment="Total hours as string to avoid precision issues"
    )
    total_gross: Mapped[str] = mapped_column(
        String(20),
        default="0.00",
        nullable=False,
        comment="Total gross salary CHF"
    )
    total_net: Mapped[str] = mapped_column(
        String(20),
        default="0.00",
        nullable=False,
        comment="Total net salary CHF"
    )
    total_employer_cost: Mapped[str] = mapped_column(
        String(20),
        default="0.00",
        nullable=False,
        comment="Total employer cost (gross + employer contributions)"
    )

    # ================================================================
    # MinIO Export Paths
    # ================================================================
    csv_export_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to CSV export"
    )
    pdf_archive_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to ZIP of all PDF payslips"
    )
    audit_log_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to audit log"
    )

    # ================================================================
    # Notes
    # ================================================================
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Admin notes for this run"
    )

    # ================================================================
    # Timestamps
    # ================================================================
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
    calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When payslips were calculated"
    )

    # ================================================================
    # Relationships
    # ================================================================
    created_by: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[created_by_id]
    )
    approved_by: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[approved_by_id]
    )
    payslips: Mapped[list["PaySlipModel"]] = relationship(
        "PaySlipModel",
        back_populates="payroll_run",
        cascade="all, delete-orphan"
    )

    # ================================================================
    # Computed Properties
    # ================================================================
    @property
    def is_editable(self) -> bool:
        """Can admin modify this run?"""
        return self.status in (PayrollRunStatus.DRAFT, PayrollRunStatus.PENDING_REVIEW)

    @property
    def is_closeable(self) -> bool:
        """Can this run be closed?"""
        return self.status == PayrollRunStatus.PAID

    def __repr__(self) -> str:
        return f"<PayrollRun {self.period_name} [{self.status.value}]>"
