# File: src/db/models/purchase_order_model.py
"""
PurchaseOrderModel - What we want from suppliers.
"Felix says add these 2-3 items to Mosey shipment"

The order that starts the import flow.
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class POStatus(str, enum.Enum):
    """Purchase order status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    PARTIALLY_SHIPPED = "partially_shipped"
    SHIPPED = "shipped"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PurchaseOrderModel(Base):
    """
    A purchase order to a supplier.
    "Felix says add these 2-3 items to Mosey shipment"
    """
    __tablename__ = 'purchase_orders'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # PO Identity
    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="e.g., PO-2025-MOSEY-003"
    )

    # Supplier
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('equipment_suppliers.id'),
        nullable=False
    )
    supplier_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Denormalized for display"
    )

    # Requested by
    requested_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Who requested this (e.g., Felix)"
    )
    requested_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # Destination
    destination_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="bar, farm, warehouse, etc."
    )
    destination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    destination_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="e.g., Mosey 420, Artemis"
    )

    # Line items (stored as JSON for flexibility)
    line_items: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of line items with qty, price, etc."
    )
    items_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Totals
    subtotal: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False
    )
    shipping_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    duties_estimate: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False
    )

    # Status
    status: Mapped[POStatus] = mapped_column(
        SQLEnum(POStatus),
        default=POStatus.DRAFT,
        nullable=False
    )

    # Dates
    expected_ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Shipping preference
    preferred_shipment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="container_20ft, pallet, etc."
    )

    # Consolidation
    consolidate_with_po: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Add to existing shipment (e.g., Mosey shipment)"
    )

    # Receipt tracking
    items_shipped: Mapped[int] = mapped_column(Integer, default=0)
    items_received: Mapped[int] = mapped_column(Integer, default=0)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal notes (e.g., YUKI handling this one)"
    )

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
    supplier: Mapped["EquipmentSupplierModel"] = relationship(back_populates="purchase_orders")
    equipment: Mapped[list["EquipmentModel"]] = relationship(back_populates="purchase_order")
    shipments: Mapped[list["ShipmentModel"]] = relationship(back_populates="purchase_orders")

    def __repr__(self):
        return f"<PurchaseOrderModel(po='{self.po_number}', supplier='{self.supplier_name}', status={self.status})>"
