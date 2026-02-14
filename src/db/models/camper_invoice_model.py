# File: src/db/models/camper_invoice_model.py
"""
CamperInvoiceModel - Invoices with IVA 22% for Camper & Tour.
Generated from completed jobs, applies deposit, calculates amount due.

"Say what you do. Do what you say. Prove it."
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


class PaymentStatus(str, enum.Enum):
    """Invoice payment lifecycle"""
    PENDING = "pending"
    DEPOSIT_PAID = "deposit_paid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


class CamperInvoiceModel(Base):
    """
    An invoice for a completed service job at Camper & Tour.
    Includes IVA 22% calculation and deposit deduction.
    """
    __tablename__ = 'camper_invoices'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    invoice_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential: INV-20260214-0001"
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
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_quotations.id'),
        nullable=True,
        comment="Optional link to original quotation"
    )

    # Line items as JSONB
    # [{description, quantity, unit_price, line_total, item_type}]
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
        comment="Italian IVA 22%"
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

    # Deposit deduction
    deposit_applied: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False,
        comment="Amount deducted from deposit already paid"
    )
    amount_due: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False,
        comment="total - deposit_applied"
    )

    # Payment
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name='camper_payment_status', create_constraint=True),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="cash, card, transfer"
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    due_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    # Document
    pdf_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="MinIO object key"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    created_by: Mapped[str] = mapped_column(
        String(100), nullable=False
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
    job: Mapped["CamperServiceJobModel"] = relationship(back_populates="invoices")
    customer: Mapped["CamperCustomerModel"] = relationship()
    quotation: Mapped["CamperQuotationModel"] = relationship()

    def __repr__(self):
        return f"<CamperInvoice(number='{self.invoice_number}', total={self.total}, status={self.payment_status})>"
