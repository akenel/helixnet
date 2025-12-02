# File: src/db/models/time_entry_model.py
# BLQ HR Module - Time Entry Model
# Built for Pam, Felix, and Mosey
"""
Time entry tracking for Swiss payroll.
Employees log hours. Managers approve. Simple.

BLQ Rule: Cameras verify. No buddy punching. LOGISH (Logical Swiss Ways).
"""
import uuid
import enum
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Date, Numeric, Enum, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .employee_model import EmployeeModel
    from .user_model import UserModel


class EntryType(str, enum.Enum):
    """Type of time entry."""
    REGULAR = "regular"         # Normal work hours (on-site)
    REMOTE = "remote"           # Remote work (80% rate)
    HOLIDAY = "holiday"         # Paid holiday (Ferien)
    SICK = "sick"               # Sick leave (Krankheit)
    UNPAID = "unpaid"           # Unpaid leave
    PUBLIC_HOLIDAY = "public_holiday"  # Swiss public holiday
    OVERTIME = "overtime"       # Approved overtime
    TRAINING = "training"       # Training/KB work


class EntryStatus(str, enum.Enum):
    """Approval status of time entry."""
    DRAFT = "draft"             # Employee can edit
    SUBMITTED = "submitted"     # Awaiting manager approval
    APPROVED = "approved"       # Manager approved, ready for payroll
    REJECTED = "rejected"       # Manager rejected, needs revision
    PAID = "paid"               # Included in closed payroll run


class TimeEntryModel(Base):
    """
    Single time entry for one employee, one day.

    Workflow:
    1. Employee creates entry (DRAFT)
    2. Employee submits (SUBMITTED)
    3. Manager approves/rejects (APPROVED/REJECTED)
    4. Payroll run includes all APPROVED entries (PAID)

    Swiss rules:
    - Max 45 hours/week (Arbeitsgesetz)
    - Overtime needs approval
    - Public holidays are paid
    """
    __tablename__ = "time_entries"

    # Index for fast queries by employee + month
    __table_args__ = (
        Index("ix_time_entries_employee_date", "employee_id", "entry_date"),
        Index("ix_time_entries_status", "status"),
    )

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
    # Employee Reference
    # ================================================================
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ================================================================
    # Time Entry Data
    # ================================================================
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="The date this entry is for"
    )

    entry_type: Mapped[str] = mapped_column(
        String(20),
        default="regular",
        nullable=False
    )

    hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Hours worked (e.g., 8.50 = 8h 30min)"
    )

    # Optional: Start and end time for detailed tracking
    start_time: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="Start time HH:MM (optional)"
    )
    end_time: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="End time HH:MM (optional)"
    )

    # Break time (Swiss law: 30min break for >5.5h, 1h for >7h)
    break_minutes: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Break time in minutes"
    )

    # ================================================================
    # Approval Workflow
    # ================================================================
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Manager who approved/rejected
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Manager's reason for rejection"
    )

    # ================================================================
    # Payroll Reference
    # ================================================================
    payslip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payslips.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link to payslip when paid"
    )

    # ================================================================
    # Description & Notes
    # ================================================================
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="What was worked on (optional)"
    )

    # KB bonus tracking
    kb_contribution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kb_contributions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Link to KB contribution for bonus"
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

    # ================================================================
    # Relationships
    # ================================================================
    employee: Mapped["EmployeeModel"] = relationship(
        "EmployeeModel",
        back_populates="time_entries"
    )

    approved_by: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        foreign_keys=[approved_by_id]
    )

    # ================================================================
    # Computed Properties
    # ================================================================
    @property
    def is_editable(self) -> bool:
        """Can employee edit this entry?"""
        return self.status == EntryStatus.DRAFT

    @property
    def is_approvable(self) -> bool:
        """Can manager approve this entry?"""
        return self.status == EntryStatus.SUBMITTED

    @property
    def effective_hours(self) -> Decimal:
        """Hours after break deduction."""
        break_hours = Decimal(self.break_minutes) / Decimal("60")
        return max(Decimal("0"), self.hours - break_hours)

    @property
    def year_month(self) -> str:
        """Year-month string for grouping (e.g., '2025-01')."""
        return self.entry_date.strftime("%Y-%m")

    def __repr__(self) -> str:
        return f"<TimeEntry {self.entry_date} {self.hours}h [{self.status.value}]>"
