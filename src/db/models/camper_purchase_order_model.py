# File: src/db/models/camper_purchase_order_model.py
"""
CamperPurchaseOrderModel - Purchase orders for parts/materials for Camper & Tour.
Tracks supplier orders from creation through delivery.

"If one seal fails, check all the seals."
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


class CamperPOStatus(str, enum.Enum):
    """Purchase order lifecycle"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    PARTIAL_RECEIVED = "partial_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class CamperPurchaseOrderModel(Base):
    """
    A purchase order for parts/materials needed for a service job.
    """
    __tablename__ = 'camper_purchase_orders'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    po_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential: PO-20260214-0001"
    )

    # Foreign Keys
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_service_jobs.id'),
        nullable=False,
        index=True
    )

    # Supplier info
    supplier_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    supplier_contact: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    supplier_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    supplier_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # Line items as JSONB
    # [{description, part_number, quantity, unit_price, line_total}]
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
        Numeric(5, 2), default=Decimal("22.00"), nullable=False
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

    # Status tracking
    status: Mapped[CamperPOStatus] = mapped_column(
        SQLEnum(CamperPOStatus, name='camper_po_status', create_constraint=True),
        default=CamperPOStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Delivery tracking
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
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
    job: Mapped["CamperServiceJobModel"] = relationship(back_populates="purchase_orders")

    def __repr__(self):
        return f"<CamperPO(number='{self.po_number}', supplier='{self.supplier_name}', status={self.status})>"
