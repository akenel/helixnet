# File: src/db/models/isotto_order_line_item_model.py
"""
IsottoOrderLineItemModel - THE core model for personalized merch orders.
Each line item = one person's customized garment in a team order.

"ASD Trapani Calcio: 20 players, 20 names, 20 numbers, 7 different sizes.
On paper = mistakes every time. In the system = perfect every time."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.core.constants import HelixEnum

from .base import Base


class LineItemStatus(HelixEnum):
    """Line item lifecycle -- each item tracked independently"""
    PENDING = "pending"
    STOCK_ORDERED = "stock_ordered"
    STOCK_RECEIVED = "stock_received"
    PRINTING = "printing"
    QUALITY_CHECK = "quality_check"
    DONE = "done"
    CANCELLED = "cancelled"


class IsottoOrderLineItemModel(Base):
    """
    A single personalized item in an ISOTTO order.
    For team orders: one row per player (name, number, size, color).
    For regular orders: one row per distinct item variation.
    """
    __tablename__ = 'isotto_order_line_items'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Parent order
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_orders.id'),
        nullable=False,
        index=True
    )

    # Catalog reference (nullable for fully custom items)
    catalog_product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_catalog_products.id'),
        nullable=True,
        index=True
    )

    # Display order
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Roster display order"
    )

    # Item specs
    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Garment color"
    )
    size: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Garment size: S, M, L, XL..."
    )

    # Personalization
    name_text: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Name on the garment: 'ROSSI'"
    )
    number_text: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Number on the garment: '10'"
    )
    custom_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Any extra custom text"
    )
    font_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Font for personalization text"
    )
    text_color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Color for personalization text"
    )
    artwork_placement: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Placement: front, back, left_sleeve, right_sleeve"
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="base + personalization markup"
    )

    # Status (independent per item)
    status: Mapped[LineItemStatus] = mapped_column(
        SQLEnum(LineItemStatus, name='isotto_line_item_status', create_constraint=True),
        default=LineItemStatus.PENDING,
        nullable=False,
        index=True
    )

    # Preview (Sprint 3)
    preview_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to preview PNG"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Per-item special instructions"
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
    order: Mapped["IsottoOrderModel"] = relationship(back_populates="line_items")
    catalog_product: Mapped["IsottoCatalogProductModel"] = relationship()

    def __repr__(self):
        name = self.name_text or "no-name"
        num = self.number_text or "-"
        return f"<IsottoLineItem(order={self.order_id}, name='{name}', num='{num}', size='{self.size}', status={self.status})>"
