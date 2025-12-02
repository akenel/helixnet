# File: src/db/models/employee_model.py
# BLQ HR Module - Employee Model
# Built for Pam, Felix, and Mosey
"""
Employee data model for Swiss-compliant HR/Payroll.
KISS: Keep It Clean, Keep It Simple.
"""
import uuid
import enum
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Date, Boolean, Numeric, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .user_model import UserModel
    from .time_entry_model import TimeEntryModel
    from .payslip_model import PaySlipModel


class ContractType(str, enum.Enum):
    """Employment contract types."""
    FULLTIME = "fulltime"       # 40 hours/week standard
    PARTTIME = "parttime"       # Less than 40 hours/week
    HOURLY = "hourly"           # Paid by hour, no guaranteed hours
    INTERN = "intern"           # Praktikum
    TEMPORARY = "temporary"     # Fixed term contract


class EmployeeStatus(str, enum.Enum):
    """Employee lifecycle status."""
    ACTIVE = "active"           # Currently employed
    PROBATION = "probation"     # In probation period (Probezeit)
    ON_LEAVE = "on_leave"       # Extended leave
    TERMINATED = "terminated"   # Employment ended
    PENDING = "pending"         # Onboarding not complete


class EmployeeModel(Base):
    """
    Employee master data.

    Links to UserModel for Keycloak auth.
    One employee = one person = one payslip per month.

    Swiss-specific fields:
    - AHV number (social security)
    - Canton for tax purposes
    - Quellensteuer flag (withholding tax for foreigners)
    """
    __tablename__ = "employees"

    # ================================================================
    # Primary Key
    # ================================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
        comment="Employee UUID"
    )

    # ================================================================
    # Link to UserModel (Keycloak auth)
    # ================================================================
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
        comment="Link to UserModel for system login"
    )

    # ================================================================
    # Personal Information
    # ================================================================
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    nationality: Mapped[str] = mapped_column(String(50), default="CH", nullable=False)

    # Swiss Social Security Number: 756.XXXX.XXXX.XX
    ahv_number: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        nullable=False,
        comment="AHV/AVS number (756.XXXX.XXXX.XX)"
    )

    # ================================================================
    # Contact Information
    # ================================================================
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Address
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    canton: Mapped[str] = mapped_column(
        String(2),
        default="LU",  # Luzern default for 420
        nullable=False,
        comment="Swiss canton code (LU, ZH, BE, etc.)"
    )

    # ================================================================
    # Banking
    # ================================================================
    iban: Mapped[str] = mapped_column(
        String(34),
        nullable=False,
        comment="IBAN for salary payment"
    )
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ================================================================
    # Employment Details
    # ================================================================
    employee_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="Internal employee ID (e.g., EMP-001)"
    )

    contract_type: Mapped[str] = mapped_column(
        String(20),
        default="fulltime",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="probation",
        nullable=False
    )

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    probation_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Probezeit end (usually start_date + 3 months)"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Last day of employment (if terminated)"
    )

    # ================================================================
    # Compensation
    # ================================================================
    hours_per_week: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("40.00"),
        nullable=False,
        comment="Contracted hours per week"
    )

    hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Base hourly rate in CHF"
    )

    # Remote work
    remote_days_per_week: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Allowed remote days per week"
    )
    remote_rate_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(4, 2),
        default=Decimal("0.80"),
        nullable=False,
        comment="Pay rate for remote hours (0.80 = 80%)"
    )

    # ================================================================
    # Benefits & Deductions
    # ================================================================
    health_insurance_contribution: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Employer health insurance contribution (CHF/month)"
    )

    health_insurance_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True after probation ends (50% covered)"
    )

    # Swiss tax specifics
    is_quellensteuer: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Subject to withholding tax (non-CH/non-C permit)"
    )

    quellensteuer_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Quellensteuer tariff code (A0, B1, C0, etc.)"
    )

    # ================================================================
    # BVG Pension (simplified)
    # ================================================================
    bvg_insured: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Enrolled in BVG pension scheme"
    )

    bvg_contribution_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0700"),  # 7% default
        nullable=False,
        comment="Employee BVG contribution rate (age-dependent)"
    )

    # ================================================================
    # Emergency Contact
    # ================================================================
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ================================================================
    # Notes
    # ================================================================
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal HR notes"
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
    user: Mapped[Optional["UserModel"]] = relationship(
        "UserModel",
        backref="employee",
        uselist=False
    )

    time_entries: Mapped[list["TimeEntryModel"]] = relationship(
        "TimeEntryModel",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    payslips: Mapped[list["PaySlipModel"]] = relationship(
        "PaySlipModel",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    # ================================================================
    # Computed Properties
    # ================================================================
    @property
    def full_name(self) -> str:
        """Full name for display."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_probation_complete(self) -> bool:
        """Check if probation period is complete."""
        if not self.probation_end_date:
            return True
        return date.today() >= self.probation_end_date

    @property
    def monthly_base_salary(self) -> Decimal:
        """Calculate monthly base salary (for full-time equivalent)."""
        # 40 hours/week * 52 weeks / 12 months = 173.33 hours/month
        monthly_hours = (self.hours_per_week * Decimal("52")) / Decimal("12")
        return monthly_hours * self.hourly_rate

    def __repr__(self) -> str:
        return f"<Employee {self.employee_number}: {self.full_name}>"
