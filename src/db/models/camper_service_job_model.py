# File: src/db/models/camper_service_job_model.py
"""
CamperServiceJobModel - Service jobs for Camper & Tour, Trapani.
The heart of the system: what work was done, by whom, what's outstanding.

Adapted from MaintenanceEventModel -- same DNA, camper shop domain.

"If one seal fails, check all the seals."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class JobType(str, enum.Enum):
    """What kind of service job"""
    REPAIR = "repair"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    INSTALLATION = "installation"
    BODYWORK = "bodywork"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    GAS_SYSTEM = "gas_system"
    WARRANTY = "warranty"
    OTHER = "other"


class JobStatus(str, enum.Enum):
    """Job lifecycle: QUOTED -> APPROVED -> IN_PROGRESS -> INSPECTION -> COMPLETED -> INVOICED"""
    QUOTED = "quoted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    INSPECTION = "inspection"
    COMPLETED = "completed"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class CamperServiceJobModel(Base):
    """
    A service job on a vehicle at Camper & Tour.
    Tracks the full lifecycle from quote to invoice.
    """
    __tablename__ = 'camper_service_jobs'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Job identity
    job_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential: JOB-20260213-0001"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Short description: 'Bathroom window seal replacement'"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the work needed"
    )

    # What vehicle / which customer
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_vehicles.id'),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_customers.id'),
        nullable=False,
        index=True
    )

    # Bay assignment (which physical workspace)
    bay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_bays.id'),
        nullable=True,
        index=True,
        comment="Current bay assignment"
    )

    # Classification
    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType, name='camper_job_type', create_constraint=True),
        nullable=False,
        default=JobType.REPAIR
    )
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name='camper_job_status', create_constraint=True),
        default=JobStatus.QUOTED,
        nullable=False,
        index=True
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Mechanic name"
    )

    # Estimation (the quote)
    estimated_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    estimated_parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    estimated_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    quote_valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Actuals (filled as work progresses)
    actual_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    actual_parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    actual_labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    actual_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="EUR", nullable=False
    )

    # Parts
    parts_used: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated parts list (v1 -- simple text)"
    )
    parts_on_order: Mapped[bool] = mapped_column(Boolean, default=False)
    parts_po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Purchase order number for parts"
    )

    # Timeline
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Calendar days expected (not labor hours)"
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="First day of work"
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Expected completion date"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    picked_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Wait tracking
    current_wait_reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Set when waiting, cleared when work resumes"
    )
    current_wait_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Estimated resume date"
    )

    # Check-in / Check-out (CYA documentation)
    mileage_in: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Odometer reading at drop-off (km)"
    )
    mileage_out: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Odometer reading at pickup (km)"
    )
    condition_notes_in: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Pre-existing damage documented at check-in: scratches, dents, leaks"
    )
    condition_notes_out: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Vehicle condition at checkout -- CYA for 'you broke my mirror'"
    )
    checked_in_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who performed the vehicle check-in"
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the vehicle was physically checked in"
    )

    # Documentation
    issue_found: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_performed: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_photos: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Comma-separated URLs"
    )
    after_photos: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="What the customer reported"
    )
    mechanic_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Internal mechanic observations"
    )

    # Inspection workflow
    inspection_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    inspection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    inspected_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Manager who performed inspection"
    )
    inspected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Deposit tracking
    deposit_required: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False,
        comment="25% of quotation total on acceptance"
    )
    deposit_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    deposit_paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Warranty tracking
    warranty_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Warranty period in months (1=30 days, 24=2 years)"
    )
    warranty_expires_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Auto-calculated: completed_at + warranty_months"
    )
    warranty_terms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="e.g., 'Parts only', 'Full labor + parts', 'Seal only, not bodywork'"
    )

    # Follow-up
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)

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
    vehicle: Mapped["CamperVehicleModel"] = relationship(back_populates="service_jobs")
    customer: Mapped["CamperCustomerModel"] = relationship(back_populates="service_jobs")
    bay: Mapped["CamperBayModel"] = relationship(back_populates="service_jobs", foreign_keys=[bay_id])
    quotations: Mapped[list["CamperQuotationModel"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    purchase_orders: Mapped[list["CamperPurchaseOrderModel"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    invoices: Mapped[list["CamperInvoiceModel"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    work_logs: Mapped[list["CamperWorkLogModel"]] = relationship(back_populates="job", cascade="all, delete-orphan", order_by="CamperWorkLogModel.logged_at")

    def __repr__(self):
        return f"<CamperServiceJob(number='{self.job_number}', title='{self.title}', status={self.status})>"
