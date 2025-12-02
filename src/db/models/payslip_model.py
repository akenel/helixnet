# File: src/db/models/payslip_model.py
# BLQ HR Module - PaySlip Model
# Built for Pam, Felix, and Mosey
"""
Individual monthly payslip for one employee.
Swiss-compliant with all required deductions.

Felix Rule: One employee = one payslip = one PDF = one email.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Boolean, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .employee_model import EmployeeModel
    from .payroll_run_model import PayrollRunModel
    from .time_entry_model import TimeEntryModel


class PaySlipModel(Base):
    """
    Individual monthly payslip.

    Contains:
    - Hours breakdown by type
    - Gross salary calculation
    - All Swiss deductions (employee share)
    - Net salary
    - Employer costs (for reporting)
    - KB bonus (CRACK contribution rewards)

    Swiss deductions (employee share):
    - AHV/IV/EO: 5.3%
    - ALV: 1.1% (up to 148,200 CHF/year)
    - BVG: ~7% (age-dependent)
    - NBU: varies (often employer pays)
    - KTG: varies (if applicable)
    """
    __tablename__ = "payslips"

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
    # References
    # ================================================================
    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payroll_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ================================================================
    # Period (denormalized for quick access)
    # ================================================================
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # ================================================================
    # Employee Snapshot (at time of payroll)
    # ================================================================
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_number: Mapped[str] = mapped_column(String(20), nullable=False)
    ahv_number: Mapped[str] = mapped_column(String(16), nullable=False)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # ================================================================
    # Hours Breakdown
    # ================================================================
    regular_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    remote_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    holiday_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    sick_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    public_holiday_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    overtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    training_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    unpaid_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )
    total_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0"), nullable=False
    )

    # ================================================================
    # Gross Salary Components
    # ================================================================
    regular_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    remote_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Remote hours at 80% rate"
    )
    holiday_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    sick_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    public_holiday_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    overtime_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Overtime at 125% rate"
    )
    training_pay: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )

    gross_salary: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Total gross before deductions"
    )

    # ================================================================
    # Employee Deductions (their share)
    # ================================================================
    ahv_iv_eo: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="AHV/IV/EO 5.3%"
    )
    alv: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="ALV 1.1%"
    )
    alv2: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="ALV2 0.5% (income >148,200)"
    )
    bvg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="BVG pension employee share"
    )
    uvg_nbu: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="NBU if employee pays"
    )
    ktg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="KTG daily sickness if applicable"
    )
    quellensteuer: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Withholding tax for foreigners"
    )
    other_deductions: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Any other deductions"
    )
    total_deductions: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Sum of all employee deductions"
    )

    # ================================================================
    # Additions
    # ================================================================
    kb_bonus: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="CRACK KB contribution bonus"
    )
    expense_reimbursement: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Expense reimbursements (not taxed)"
    )
    other_additions: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )

    # ================================================================
    # Net Salary
    # ================================================================
    net_salary: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Final amount to pay"
    )

    # ================================================================
    # Employer Costs (for reporting, not on payslip)
    # ================================================================
    employer_ahv: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Employer AHV share 5.3%"
    )
    employer_alv: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Employer ALV share"
    )
    employer_bvg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Employer BVG share"
    )
    employer_uvg: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Employer UVG (accident)"
    )
    employer_fak: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Family compensation fund"
    )
    employer_admin: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
        comment="Admin costs"
    )
    total_employer_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Gross + all employer contributions"
    )

    # ================================================================
    # Delivery Status
    # ================================================================
    pdf_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    pdf_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="MinIO path to PDF"
    )
    email_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ================================================================
    # Notes
    # ================================================================
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Notes visible on payslip"
    )
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Internal HR notes (not on payslip)"
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
    payroll_run: Mapped["PayrollRunModel"] = relationship(
        "PayrollRunModel",
        back_populates="payslips"
    )
    employee: Mapped["EmployeeModel"] = relationship(
        "EmployeeModel",
        back_populates="payslips"
    )
    time_entries: Mapped[list["TimeEntryModel"]] = relationship(
        "TimeEntryModel",
        foreign_keys="TimeEntryModel.payslip_id",
        backref="payslip"
    )

    # ================================================================
    # Computed Properties
    # ================================================================
    @property
    def period_display(self) -> str:
        """Human-readable period."""
        months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
                  "Juli", "August", "September", "Oktober", "November", "Dezember"]
        return f"{months[self.month]} {self.year}"

    @property
    def iban_display(self) -> str:
        """Get IBAN from employee (for display)."""
        if self.employee:
            return self.employee.iban
        return ""

    def __repr__(self) -> str:
        return f"<PaySlip {self.employee_name} {self.year}-{self.month:02d} CHF {self.net_salary}>"
