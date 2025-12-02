# File: src/db/models/product_model.py
"""
ProductModel - Represents items in Felix's Artemis store catalog.
Designed to eventually import from Tamara database dump (Q2-2026).
For demo: manually seed 5-10 items.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class ProductModel(Base):
    """
    Product catalog for POS system.
    Supports both barcoded items (~70% of inventory) and manual entry.
    """
    __tablename__ = 'products'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Product Identity
    barcode: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
        comment="EAN/UPC barcode - nullable for non-barcoded items"
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="Internal SKU - always required even if no barcode"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Product name as displayed to customer"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full product description (from Artemis website)"
    )

    # Pricing
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Sale price in CHF"
    )
    cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Cost price for margin calculations (optional)"
    )

    # Inventory
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current stock on hand"
    )
    stock_alert_threshold: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Alert when stock falls below this level"
    )

    # Categorization
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Product category (CBD, accessories, etc.)"
    )
    tags: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated tags for search/filtering"
    )

    # Product Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Product available for sale"
    )
    is_age_restricted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Requires 18+ ID verification (CBD products)"
    )

    # Vending Machine Compatibility
    vending_compatible: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Can be sold via Marco's vending machine"
    )
    vending_slot: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Vending machine slot number (if applicable)"
    )

    # Supplier Integration (FourTwenty, etc.)
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
        comment="Supplier's SKU (e.g., FourTwenty product ID)"
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Supplier name (e.g., 'FourTwenty', 'Sylvie')"
    )
    supplier_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Last known supplier price (for change detection)"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last sync from supplier feed"
    )
    sync_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="If True, skip supplier updates (local price/info maintained)"
    )

    # Stock Management
    min_stock: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum stock level (alert threshold)"
    )
    max_stock: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Maximum/target stock level"
    )
    lead_time_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Supplier lead time in days"
    )

    # Product Images
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Primary product image URL"
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
    line_items: Mapped[list["LineItemModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ProductModel(sku='{self.sku}', name='{self.name}', price={self.price} CHF)>"
