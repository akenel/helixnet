# File: src/db/models/line_item_model.py
"""
LineItemModel - Individual products in a transaction cart.
Similar to TaskModel - represents one product added to a sale.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class LineItemModel(Base):
    """
    Individual product in a transaction cart.
    One transaction has many line items (one per product scanned).
    """
    __tablename__ = 'line_items'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('transactions.id'),
        nullable=False,
        comment="Parent transaction this item belongs to"
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id'),
        nullable=False,
        comment="Product from catalog"
    )

    # Line Item Details
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="How many units of this product"
    )
    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price per unit at time of sale (snapshot from product)"
    )
    discount_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=0.00,
        nullable=False,
        comment="Percentage discount applied (loyalty, promo)"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00,
        nullable=False,
        comment="Total discount in CHF for this line"
    )
    line_total: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Final price: (quantity * unit_price) - discount_amount"
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Special notes for this item (e.g., 'gift wrap requested')"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When item was added to cart"
    )

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(
        back_populates="line_items"
    )
    product: Mapped["ProductModel"] = relationship(
        back_populates="line_items"
    )

    def __repr__(self):
        return f"<LineItemModel(product_id='{self.product_id}', quantity={self.quantity}, total={self.line_total} CHF)>"
