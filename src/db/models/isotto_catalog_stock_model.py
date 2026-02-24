# File: src/db/models/isotto_catalog_stock_model.py
"""
IsottoCatalogStockModel - Per size+color stock tracking for ISOTTO catalog products.
One product can have up to 70 combos (10 colors x 7 sizes).

"If one seal fails, check all the seals." -- applies to stock too.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class IsottoCatalogStockModel(Base):
    """
    Stock level for a specific product + color + size combination.
    UniqueConstraint ensures no duplicate entries per combo.
    """
    __tablename__ = 'isotto_catalog_stock'
    __table_args__ = (
        UniqueConstraint('product_id', 'color', 'size', name='uq_isotto_stock_product_color_size'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_catalog_products.id'),
        nullable=False,
        index=True
    )

    color: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Color name: 'white', 'navy', 'red'"
    )
    size: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Size: 'S', 'M', 'L', 'XL'"
    )

    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Physical stock on hand"
    )
    quantity_reserved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Reserved for pending orders"
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
    product: Mapped["IsottoCatalogProductModel"] = relationship(back_populates="stock_entries")

    @property
    def available(self) -> int:
        """Stock available for new orders"""
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    def __repr__(self):
        return f"<IsottoStock(product={self.product_id}, color='{self.color}', size='{self.size}', qty={self.quantity_on_hand})>"
