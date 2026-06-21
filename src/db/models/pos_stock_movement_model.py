# File: src/db/models/pos_stock_movement_model.py
"""
PosStockMovementModel — Banco-native stock movement ledger (BL-91 receiving).

Why a NEW table (not inventory_model.StockMovementModel): that one FKs to
`inventory_items` — a different subsystem with its own item identity. Banco's POS
operates on `products`, so receiving needs a movement row that FKs to products.

Lean by design (the locked BL-91 scope): record stock going IN at the counter
(scan -> type the count -> stock up), with an audit trail of who/when/how-much and
the resulting on-hand. No purchase orders, no costing — those come later. The same
table can later record OUT movements (sales/refunds/adjustments) so there's one
honest history of every stock change, but BL-91 only writes receiving ('in').
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class PosStockMovementModel(Base):
    __tablename__ = 'pos_stock_movements'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        String(8), default='in', nullable=False,
        comment="'in' (receiving/restock) or 'out' (sale/adjustment)",
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Units moved (always positive; direction carries the sign)",
    )
    quantity_after: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="products.stock_quantity AFTER this movement (audit snapshot)",
    )
    reason: Mapped[str] = mapped_column(
        String(40), default='receiving', nullable=False,
        comment="'receiving', 'adjustment', 'sale', 'refund', ...",
    )
    reference: Mapped[str | None] = mapped_column(
        String(140), nullable=True,
        comment="Free-text note / delivery ref (e.g. supplier, invoice no.)",
    )
    performed_by: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Username of the operator who recorded the movement",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    product: Mapped["ProductModel"] = relationship()

    def __repr__(self):
        return (f"<PosStockMovementModel({self.direction} {self.quantity} "
                f"-> {self.quantity_after}, product={self.product_id})>")
