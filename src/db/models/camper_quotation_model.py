# File: src/db/models/camper_quotation_model.py
"""
CamperQuotationModel - Formal quotations with line items for Camper & Tour.
Each quotation links to a job and contains itemized pricing with IVA calculation.

"One shot, one kill." - UFA Wolf Philosophy
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Text, Numeric
from sqlalchemy import Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class QuotationStatus(str, enum.Enum):
    """Quotation lifecycle"""
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CamperQuotationModel(Base):
    """
    A formal quotation for a service job at Camper & Tour.
    Contains line items (labor, parts, materials) with IVA calculation.
    """
    __tablename__ = 'camper_quotations'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    quote_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential: QUO-20260214-0001"
    )

    # Foreign Keys
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_service_jobs.id'),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_customers.id'),
        nullable=False,
        index=True
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_vehicles.id'),
        nullable=False,
        index=True
    )

    # Line items as JSONB
    # [{description, quantity, unit_price, line_total, item_type: "labor"|"parts"|"materials"}]
    line_items: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False
    )

    # Financials
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("22.00"), nullable=False,
        comment="Italian IVA standard rate"
    )
    vat_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="EUR", nullable=False
    )

    # Deposit
    deposit_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("25.00"), nullable=False,
        comment="Default 25% deposit on acceptance"
    )
    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )

    # Validity
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[QuotationStatus] = mapped_column(
        SQLEnum(QuotationStatus, name='camper_quotation_status', create_constraint=True),
        default=QuotationStatus.DRAFT,
        nullable=False,
        index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Document
    pdf_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="MinIO object key"
    )

    # Audit
    created_by: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Username who created"
    )
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
    job: Mapped["CamperServiceJobModel"] = relationship(back_populates="quotations")
    customer: Mapped["CamperCustomerModel"] = relationship()
    vehicle: Mapped["CamperVehicleModel"] = relationship()

    def __repr__(self):
        return f"<CamperQuotation(number='{self.quote_number}', status={self.status}, total={self.total})>"
