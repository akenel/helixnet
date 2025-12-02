# File: src/schemas/hr_schema.py
"""
HR/Payroll Schemas - BLQ Module

Swiss-compliant time tracking and payroll.
Built for Pam (enters time), Felix (approves), Mosey (signs off).

"Be water, my friend" - Bruce Lee
"KICKIS: Keep It Clean, Keep It Simple" - BLQ Philosophy
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional, List
from enum import Enum


# ================================================================
# ENUMS - Time Entry Types & Status
# ================================================================

class EntryType(str, Enum):
    """What kind of work day?"""
    REGULAR = "regular"              # Normal office/store work
    REMOTE = "remote"                # Home office (80% rate)
    HOLIDAY = "holiday"              # Paid vacation
    SICK = "sick"                    # Krankheit
    UNPAID = "unpaid"                # Unbezahlt
    PUBLIC_HOLIDAY = "public_holiday"  # Feiertag (100% paid)
    OVERTIME = "overtime"            # Overtime (125% rate)
    TRAINING = "training"            # Training/KB contribution


class EntryStatus(str, Enum):
    """Time entry approval workflow"""
    DRAFT = "draft"                  # Employee filling in
    SUBMITTED = "submitted"          # Ready for manager review
    APPROVED = "approved"            # Manager approved
    REJECTED = "rejected"            # Sent back for correction
    PAID = "paid"                    # Included in payroll


class ContractType(str, Enum):
    """Employment contract types"""
    FULLTIME = "fulltime"            # 100% (40h/week)
    PARTTIME = "parttime"            # <100%
    HOURLY = "hourly"                # Stundenlohn
    APPRENTICE = "apprentice"        # Lehrling
    INTERN = "intern"                # Praktikant


class EmployeeStatus(str, Enum):
    """Employee lifecycle status"""
    PROBATION = "probation"          # Probezeit (3 months)
    ACTIVE = "active"                # Regular employee
    NOTICE = "notice"                # In Kuendigung
    TERMINATED = "terminated"        # Ausgetreten
    ON_LEAVE = "on_leave"            # Sabbatical/Elternzeit


# ================================================================
# TIME ENTRY SCHEMAS
# ================================================================

class TimeEntryBase(BaseModel):
    """Base time entry data"""
    entry_date: date = Field(..., description="The work day")
    entry_type: EntryType = Field(default=EntryType.REGULAR)
    hours: Decimal = Field(..., ge=0, le=24, description="Hours worked (0.25 increments)")
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    break_minutes: int = Field(default=0, ge=0, le=120, description="Break time in minutes")
    description: Optional[str] = Field(None, max_length=500, description="Work description")


class TimeEntryCreate(TimeEntryBase):
    """Create a new time entry"""
    kb_contribution_id: Optional[UUID] = Field(None, description="Link to KB if training type")


class TimeEntryUpdate(BaseModel):
    """Update time entry (all optional)"""
    entry_date: Optional[date] = None
    entry_type: Optional[EntryType] = None
    hours: Optional[Decimal] = Field(None, ge=0, le=24)
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    break_minutes: Optional[int] = Field(None, ge=0, le=120)
    description: Optional[str] = Field(None, max_length=500)
    kb_contribution_id: Optional[UUID] = None


class TimeEntryRead(TimeEntryBase):
    """Time entry with full metadata"""
    id: UUID
    employee_id: UUID
    status: EntryStatus

    # Approval workflow
    submitted_at: Optional[datetime] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Payroll link
    payslip_id: Optional[UUID] = None

    # KB link
    kb_contribution_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeEntryBulkCreate(BaseModel):
    """Create multiple time entries at once (week view)"""
    entries: List[TimeEntryCreate] = Field(..., min_length=1, max_length=7)


class TimeEntrySubmit(BaseModel):
    """Submit entries for approval"""
    entry_ids: List[UUID] = Field(..., min_length=1, description="Entries to submit")


class TimeEntryApproval(BaseModel):
    """Manager approval/rejection"""
    entry_ids: List[UUID] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = Field(None, max_length=500)


# ================================================================
# EMPLOYEE SCHEMAS
# ================================================================

class EmployeeBase(BaseModel):
    """Base employee data"""
    # Personal
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: date
    nationality: str = Field(default="CH", max_length=50)
    ahv_number: str = Field(..., min_length=13, max_length=16, description="756.XXXX.XXXX.XX")

    # Contact
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    street: str = Field(..., max_length=255)
    postal_code: str = Field(..., max_length=10)
    city: str = Field(..., max_length=100)
    canton: str = Field(default="LU", max_length=2)

    # Banking
    iban: str = Field(..., max_length=34, description="CH93 0076 2011 6238 5295 7")
    bank_name: Optional[str] = Field(None, max_length=100)

    # Employment
    employee_number: str = Field(..., max_length=20, description="BLQ-001")
    contract_type: ContractType = Field(default=ContractType.FULLTIME)
    start_date: date
    probation_end_date: Optional[date] = None
    end_date: Optional[date] = None

    # Compensation
    hours_per_week: Decimal = Field(default=Decimal("40.00"), ge=0, le=50)
    hourly_rate: Decimal = Field(..., ge=0, description="CHF per hour")
    remote_days_per_week: int = Field(default=0, ge=0, le=5)
    remote_rate_multiplier: Decimal = Field(default=Decimal("0.80"), description="Remote = 80%")

    # Benefits
    health_insurance_contribution: Decimal = Field(default=Decimal("0.00"))
    health_insurance_active: bool = Field(default=False)
    is_quellensteuer: bool = Field(default=False, description="Withholding tax for foreigners")
    quellensteuer_code: Optional[str] = Field(None, max_length=10)
    bvg_insured: bool = Field(default=True, description="Pension insurance")
    bvg_contribution_rate: Decimal = Field(default=Decimal("0.0700"), description="7% default")

    # Emergency
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)

    # Notes
    notes: Optional[str] = Field(None, max_length=2000)


class EmployeeCreate(EmployeeBase):
    """Create new employee"""
    user_id: Optional[UUID] = Field(None, description="Link to Keycloak user")


class EmployeeUpdate(BaseModel):
    """Update employee (all optional)"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    street: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    canton: Optional[str] = Field(None, max_length=2)
    iban: Optional[str] = Field(None, max_length=34)
    bank_name: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    remote_days_per_week: Optional[int] = Field(None, ge=0, le=5)
    health_insurance_contribution: Optional[Decimal] = None
    health_insurance_active: Optional[bool] = None
    quellensteuer_code: Optional[str] = Field(None, max_length=10)
    bvg_contribution_rate: Optional[Decimal] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=2000)
    status: Optional[EmployeeStatus] = None
    end_date: Optional[date] = None


class EmployeeRead(EmployeeBase):
    """Full employee profile"""
    id: UUID
    user_id: Optional[UUID] = None
    status: EmployeeStatus

    # Computed
    full_name: str = ""
    monthly_target_hours: Decimal = Decimal("0")

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context) -> None:
        self.full_name = f"{self.first_name} {self.last_name}"
        # Standard Swiss work month: 4.33 weeks
        self.monthly_target_hours = self.hours_per_week * Decimal("4.33")


# ================================================================
# PAYROLL RUN SCHEMAS
# ================================================================

class PayrollRunStatus(str, Enum):
    """Payroll workflow status"""
    DRAFT = "draft"                  # Creating
    CALCULATING = "calculating"      # Processing time entries
    PENDING_REVIEW = "pending_review"  # Ready for manager
    APPROVED = "approved"            # Manager approved
    PAID = "paid"                    # Payments sent
    CLOSED = "closed"                # Archived


class PayrollRunCreate(BaseModel):
    """Create a new payroll run"""
    year: int = Field(..., ge=2024, le=2100)
    month: int = Field(..., ge=1, le=12)
    notes: Optional[str] = Field(None, max_length=1000)


class PayrollRunRead(BaseModel):
    """Payroll run summary"""
    id: UUID
    year: int
    month: int
    period_name: str
    status: PayrollRunStatus

    # Totals
    total_employees: int
    total_hours: Decimal
    total_gross: Decimal
    total_net: Decimal
    total_employer_cost: Decimal

    # Workflow
    created_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Exports
    csv_export_path: Optional[str] = None
    pdf_archive_path: Optional[str] = None

    # Notes
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    calculated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PAYSLIP SCHEMAS
# ================================================================

class PaySlipRead(BaseModel):
    """Individual payslip"""
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    year: int
    month: int

    # Employee snapshot
    employee_name: str
    employee_number: str
    ahv_number: str
    hourly_rate: Decimal

    # Hours breakdown
    regular_hours: Decimal
    remote_hours: Decimal
    holiday_hours: Decimal
    sick_hours: Decimal
    public_holiday_hours: Decimal
    overtime_hours: Decimal
    training_hours: Decimal
    unpaid_hours: Decimal
    total_hours: Decimal

    # Gross components
    regular_pay: Decimal
    remote_pay: Decimal
    holiday_pay: Decimal
    sick_pay: Decimal
    public_holiday_pay: Decimal
    overtime_pay: Decimal
    training_pay: Decimal
    gross_salary: Decimal

    # Deductions
    ahv_iv_eo: Decimal
    alv: Decimal
    alv2: Decimal
    bvg: Decimal
    uvg_nbu: Decimal
    ktg: Decimal
    quellensteuer: Decimal
    other_deductions: Decimal
    total_deductions: Decimal

    # Additions
    kb_bonus: Decimal
    expense_reimbursement: Decimal
    other_additions: Decimal

    # Net
    net_salary: Decimal

    # Employer costs
    employer_ahv: Decimal
    employer_alv: Decimal
    employer_bvg: Decimal
    employer_uvg: Decimal
    employer_fak: Decimal
    employer_admin: Decimal
    total_employer_cost: Decimal

    # Delivery
    pdf_generated: bool
    pdf_path: Optional[str] = None
    email_sent: bool
    email_sent_at: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DASHBOARD VIEWS
# ================================================================

class EmployeeTimesheet(BaseModel):
    """Weekly timesheet view for employee"""
    employee_id: UUID
    employee_name: str
    week_start: date
    week_end: date

    # Entries for the week
    entries: List[TimeEntryRead]

    # Summary
    total_hours: Decimal
    target_hours: Decimal
    balance: Decimal  # Over/under target
    pending_approval: int

    model_config = ConfigDict(from_attributes=True)


class PayrollDashboard(BaseModel):
    """Manager payroll overview"""
    current_period: str

    # Time entry status
    entries_pending_approval: int
    entries_approved: int
    entries_rejected: int

    # Payroll status
    payroll_run_status: Optional[PayrollRunStatus] = None
    total_employees: int
    total_gross: Decimal
    total_net: Decimal

    # Alerts
    missing_timesheets: List[str]  # Employee names
    overtime_alerts: List[str]     # Employees with >10h overtime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SWISS PAYROLL CONSTANTS
# ================================================================

# AHV/IV/EO (Old age, disability, income replacement)
AHV_RATE_EMPLOYEE = Decimal("0.053")  # 5.3%
AHV_RATE_EMPLOYER = Decimal("0.053")  # 5.3%

# ALV (Unemployment insurance)
ALV_RATE_EMPLOYEE = Decimal("0.011")  # 1.1%
ALV_RATE_EMPLOYER = Decimal("0.011")  # 1.1%
ALV_MAX_SALARY = Decimal("148200")    # Per year
ALV2_RATE = Decimal("0.005")          # 0.5% above ALV_MAX_SALARY

# UVG (Accident insurance)
UVG_BU_RATE = Decimal("0.0")          # Employer pays
UVG_NBU_RATE = Decimal("0.0124")      # 1.24% (if employee pays NBU)

# FAK (Family compensation)
FAK_RATE_EMPLOYER = Decimal("0.012")  # 1.2% (Canton LU)

# Admin fee
ADMIN_RATE = Decimal("0.002")         # 0.2% admin costs

# Overtime multiplier
OVERTIME_MULTIPLIER = Decimal("1.25")  # 125%

# Remote rate
REMOTE_MULTIPLIER = Decimal("0.80")    # 80%
