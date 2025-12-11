# File: src/db/models/equipment_acquisition_model.py
"""
EquipmentAcquisitionModel - BUY vs LEASE vs RENT Decision Engine

Felix needs a centrifuge. 50,000 CHF.
- BUY: Own it forever, depreciate, maintain
- LEASE: Monthly payments, upgrade path, return option
- RENT: Short-term, project-based, no commitment

"Do we buy, lease, or rent?" - Felix asking the real questions

This model tracks:
1. The decision process (who decided, why)
2. The financial terms (payments, duration, total cost)
3. The outcome (did we save money? was it worth it?)
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class AcquisitionType(str, enum.Enum):
    """How we're getting the equipment"""
    BUY = "buy"              # Full purchase, we own it
    LEASE = "lease"          # Long-term rental with purchase option
    RENT = "rent"            # Short-term rental, return after
    LEASE_TO_OWN = "lease_to_own"  # Payments go toward purchase
    FINANCING = "financing"  # Bank loan for purchase
    GIFT = "gift"            # Donated (rare but happens)
    INTERNAL = "internal"    # Transferred from another location


class AcquisitionStatus(str, enum.Enum):
    """Where are we in the decision"""
    REQUESTED = "requested"      # Someone asked for it
    EVALUATING = "evaluating"    # Comparing options
    QUOTES_RECEIVED = "quotes_received"
    APPROVED = "approved"        # Go ahead given
    REJECTED = "rejected"        # Not approved
    IN_PROGRESS = "in_progress"  # Procurement happening
    COMPLETED = "completed"      # We got it
    CANCELLED = "cancelled"      # Changed our minds


class UrgencyLevel(str, enum.Enum):
    """How soon do we need it"""
    CRITICAL = "critical"    # Yesterday. Production stopped.
    HIGH = "high"            # This week. Major impact.
    MEDIUM = "medium"        # This month. Planning ahead.
    LOW = "low"              # Someday. Nice to have.


class EquipmentAcquisitionModel(Base):
    """
    Track equipment acquisition decisions.

    Felix: "I need a centrifuge for lab testing."
    SAL: "50K CHF? Let's look at our options."

    This model captures that conversation and decision.
    """
    __tablename__ = 'equipment_acquisitions'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Request Identity
    request_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="e.g., ACQ-2025-FELIX-001"
    )

    # What's being requested
    equipment_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="centrifuge, salad_bar, coffee_machine, etc."
    )
    equipment_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Specific model or description"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why we need it, what problem it solves"
    )

    # Who requested
    requested_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Felix, SAL, Molly, etc."
    )
    requested_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Lab, Kitchen, Bar, Farm, etc."
    )

    # Urgency
    urgency: Mapped[UrgencyLevel] = mapped_column(
        SQLEnum(UrgencyLevel),
        default=UrgencyLevel.MEDIUM,
        nullable=False
    )
    needed_by: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="When do we need it operational"
    )

    # Destination
    destination_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="bar, farm, lab, warehouse"
    )
    destination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    destination_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Artemis, Mosey 420, Felix's Lab"
    )

    # ================================================
    # THE DECISION: BUY vs LEASE vs RENT
    # ================================================
    acquisition_type: Mapped[AcquisitionType | None] = mapped_column(
        SQLEnum(AcquisitionType),
        nullable=True,
        comment="Final decision: buy, lease, or rent"
    )
    decision_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    decision_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who made the final call"
    )
    decision_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why this option was chosen"
    )

    # Status
    status: Mapped[AcquisitionStatus] = mapped_column(
        SQLEnum(AcquisitionStatus),
        default=AcquisitionStatus.REQUESTED,
        nullable=False
    )

    # ================================================
    # FINANCIAL COMPARISON (stored as JSON)
    # ================================================
    # Each option: { type, vendor, price, monthly, duration, total_cost, notes }
    buy_options: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of purchase options"
    )
    lease_options: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of lease options"
    )
    rent_options: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of rental options"
    )

    # Selected option details
    selected_vendor: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    selected_vendor_contact: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # ================================================
    # PURCHASE DETAILS (if buying)
    # ================================================
    purchase_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    warranty_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    expected_lifetime_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="For depreciation calculation"
    )
    annual_depreciation: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    # ================================================
    # LEASE DETAILS (if leasing)
    # ================================================
    lease_monthly_payment: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    lease_duration_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    lease_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lease_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lease_buyout_option: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    lease_buyout_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    lease_includes_maintenance: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # ================================================
    # RENTAL DETAILS (if renting)
    # ================================================
    rental_daily_rate: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    rental_weekly_rate: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    rental_monthly_rate: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    rental_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rental_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rental_extension_possible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # ================================================
    # TOTAL COST OF OWNERSHIP
    # ================================================
    estimated_annual_maintenance: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    estimated_consumables_yearly: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Filters, oils, parts"
    )
    estimated_energy_yearly: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Power costs"
    )
    total_cost_year_1: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    total_cost_5_years: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="CHF",
        nullable=False
    )

    # ================================================
    # BUSINESS CASE
    # ================================================
    revenue_impact: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="How this enables revenue"
    )
    productivity_gain: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Time/labor savings"
    )
    risk_if_not_acquired: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="What happens if we don't get it"
    )
    alternatives_considered: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Other ways to solve the problem"
    )

    # ================================================
    # APPROVAL WORKFLOW
    # ================================================
    requires_board_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="For big purchases (>10K CHF)"
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    approved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ================================================
    # PROCUREMENT TRACKING
    # ================================================
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('purchase_orders.id'),
        nullable=True
    )
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('equipment.id'),
        nullable=True,
        comment="Link to actual equipment once received"
    )

    # ================================================
    # POST-ACQUISITION REVIEW
    # ================================================
    review_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="6-month or 1-year review"
    )
    actual_vs_expected: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Did it meet expectations?"
    )
    lessons_learned: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    would_recommend: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    purchase_order: Mapped["PurchaseOrderModel"] = relationship()
    equipment: Mapped["EquipmentModel"] = relationship()

    def __repr__(self):
        return f"<EquipmentAcquisitionModel(req='{self.request_number}', type={self.acquisition_type}, status={self.status})>"

    def calculate_5_year_cost(self, acquisition_type: AcquisitionType) -> float:
        """Calculate 5-year total cost for comparison"""
        if acquisition_type == AcquisitionType.BUY:
            base = float(self.purchase_price or 0)
            maintenance = float(self.estimated_annual_maintenance or 0) * 5
            consumables = float(self.estimated_consumables_yearly or 0) * 5
            energy = float(self.estimated_energy_yearly or 0) * 5
            return base + maintenance + consumables + energy

        elif acquisition_type == AcquisitionType.LEASE:
            monthly = float(self.lease_monthly_payment or 0)
            months = min(60, self.lease_duration_months or 60)  # 5 years max
            return monthly * months

        elif acquisition_type == AcquisitionType.RENT:
            monthly = float(self.rental_monthly_rate or 0)
            return monthly * 60  # 5 years

        return 0.0
