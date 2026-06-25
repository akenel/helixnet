# File: src/db/models/product_model.py
"""
ProductModel - Represents items in Felix's Artemis store catalog.
Designed to eventually import from Tamara database dump (Q2-2026).
For demo: manually seed 5-10 items.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey
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
        default=1,
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
        comment="Requires 18+ ID verification (DERIVED from product_class on save; CRUD-overridable)"
    )
    # BL-96: behaviour CLASS (standard | tobacco_nicotine | alcohol | cbd_hemp | cafe_food).
    # Drives the age gate + VAT; see src/services/catalog_taxonomy.py for the rules.
    product_class: Mapped[str] = mapped_column(
        String(40),
        default="standard",
        nullable=False,
        comment="Behaviour class — drives 18+ gate + VAT (catalog_taxonomy.PRODUCT_CLASSES)"
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

    # La Piazza bridge (Artemis Premium) -- push-once-then-decouple.
    # When the shop publishes this product to the La Piazza marketplace it lands as a
    # DRAFT under the shop's business account; we record the listing id/slug so we can
    # find it + build the QR target. We do NOT keep syncing -- once seeded, the listing
    # is the shop owner's to maintain. A re-push creates a NEW listing, not an update.
    lapiazza_listing_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="La Piazza listing id this product was seeded as (null = never pushed)"
    )
    lapiazza_slug: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="La Piazza listing slug -- the QR target resolves to /items/{slug}"
    )
    lapiazza_pushed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this product was seeded to La Piazza (the one-shot push)"
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
    barcodes: Mapped[list["ProductBarcodeModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImageModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImageModel.sort_order, ProductImageModel.created_at",
    )

    def __repr__(self):
        return f"<ProductModel(sku='{self.sku}', name='{self.name}', price={self.price} CHF)>"


class ProductBarcodeModel(Base):
    """
    Alias barcodes — one product, many barcodes (BL-90).

    Why this exists: a single article (e.g. a box of rolling papers) often prints
    MORE THAN ONE barcode on the packaging — the retail EAN plus a logistics/case
    code. Scanning the second code on a product already in the catalog used to
    404 → the operator re-captured the SAME item under a new barcode → "scan once,
    known forever" broke. Now every extra code a product is ever scanned under can
    be attached here, and lookup checks products.barcode OR product_barcodes.

    The product's "primary" barcode stays on products.barcode; this table holds the
    additional aliases. A barcode is globally unique across BOTH places.
    """
    __tablename__ = 'product_barcodes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    barcode: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="An additional EAN/UPC this product is also known by",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="barcodes")

    def __repr__(self):
        return f"<ProductBarcodeModel(barcode='{self.barcode}', product_id='{self.product_id}')>"


class ProductImageModel(Base):
    """
    Product photos — one product, many pictures (the gallery).

    For ~100%-unmarked head-shop goods the PHOTO is the label: a couple of angles
    is how you recognise an item in the catalogue later. The bytes live in MinIO at
    `pos-products/{product_id}/{id}.jpg`; this row is the index + ordering. The
    product's cover stays on products.image_url (points at the chosen image's serve
    URL, or an external paste).
    """
    __tablename__ = 'product_images'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('products.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Display order in the gallery; lower = first",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="images")

    def __repr__(self):
        return f"<ProductImageModel(id='{self.id}', product_id='{self.product_id}')>"
