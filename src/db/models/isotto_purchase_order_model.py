# File: src/db/models/isotto_purchase_order_model.py
"""
IsottoPurchaseOrderModel - Purchase orders from ISOTTO Sport to suppliers.
Tracks blank merchandise orders from creation through delivery.

"20 players, 20 names, 20 numbers, 7 different sizes.
 Need 5 more XL whites from ROLY? Generate the PO."
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.core.constants import HelixEnum

from .base import Base


class IsottoPOStatus(HelixEnum):
    """Purchase order lifecycle"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    PARTIAL_RECEIVED = "partial_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class IsottoPurchaseOrderModel(Base):
    """
    A purchase order from ISOTTO Sport to a supplier.
    Generated manually or auto-generated from order line items.
    """
    __tablename__ = 'isotto_purchase_orders'

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
        comment="Sequential: IPO-YYYYMMDD-NNNN"
    )

    # Supplier FK
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_suppliers.id'),
        nullable=False,
        index=True
    )

    # Line items as JSONB
    # [{product_code, product_name, color, size, quantity, unit_price, line_total}]
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

    # Status
    status: Mapped[IsottoPOStatus] = mapped_column(
        SQLEnum(IsottoPOStatus, name='isotto_po_status', create_constraint=True),
        default=IsottoPOStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Delivery tracking
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Related orders (which ISOTTO orders this PO serves)
    related_order_ids: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment="Order IDs this PO serves"
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
    supplier: Mapped["IsottoSupplierModel"] = relationship()

    def __repr__(self):
        return f"<IsottoPO(number='{self.po_number}', status={self.status})>"
