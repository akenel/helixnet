# File: src/db/models/product_model.py
"""
ProductModel - Represents items in Felix's Artemis store catalog.
Designed to eventually import from Tamara database dump (Q2-2026).
For demo: manually seed 5-10 items.
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey, UniqueConstraint
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
        comment="EAN/UPC barcode - nullable for non-barcoded items (may be an internally-minted EAN-13)"
    )
    # §6b: True when `barcode` is an EAN-13 we MINTED ourselves (GS1 internal 20–29
    # prefix) because the source carried no manufacturer barcode. Lets the UI/print
    # layer distinguish "real retail code" from "our scan-sheet code" and lets a sync
    # never clobber a manufacturer barcode that was attached later.
    barcode_is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if `barcode` is an internally-minted EAN-13 (no source EAN existed)"
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
    # §9.1: category stays FLAT (group + category on the row; full source path in `tags`).
    # No categories table yet — the lossless `artemis_path` + `tags` re-derive the tree later.
    product_group: Mapped[str | None] = mapped_column(
        String(60),
        index=True,
        nullable=True,
        comment="Banco level-1 group (e.g. Headshop, CBD, Papers & Co) — flat hierarchy lvl1"
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Product category — Banco level-2, consolidated/shopper-friendly (CBD, Storage, ...)"
    )
    tags: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated tags for search/filtering (carries the verbatim artemis_path breadcrumb)"
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
    # §3: the RULE that set the 18+ gate (e.g. "class:cbd_hemp", "headshop-smoking-paraphernalia").
    # Auditable LAW-axis trail — every age flag records why it was raised.
    age_reason: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        comment="Auditable reason the 18+ gate was set (the rule/class that raised it)"
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
    price_tiers: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="BL-26 quantity-break pricing: [{min_qty, unit_price}, ...] ascending; None/empty = flat price"
    )
    tier_mode: Mapped[str | None] = mapped_column(
        String(12),
        nullable=True,
        comment="BL-26 tier interpretation: 'per_unit' (price EACH at qty>=N) | 'bundle' (N for X total). Default per_unit."
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last sync from supplier feed"
    )
    description_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="BL-18: last time the description backfill scraped this item's page "
                "(fill or empty). Lets the cron rotate the queue instead of re-scraping "
                "permanent-empties every run.",
    )
    image_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="BL-17: last time the image backfill tried to pull this item's external "
                "hotlink into MinIO (ok or failed). Same rotation trick as description_checked_at.",
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
        Text,
        nullable=True,
        comment="Primary product image URL (Text — supplier/CDN URLs routinely exceed 500 chars)"
    )

    # Rookie workbench (BL-98): a PRIVATE operator note — why an item is parked + the next step
    # ("need the delivery slip for cost", "confirm supplier", "find a sharper pic"). Bench-only,
    # never customer-facing / on a receipt. Lets whoever finishes the catalog keep tabs so they
    # never stare at an item wondering "what now".
    work_note: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Private bench note: why parked + next action (never customer-facing)"
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

    # ================================================================
    # ENRICHMENT / SOURCE PROVENANCE (Artemis feed — §3, §6a, §6c, §6d)
    # The lossless record so any later decision (categories table, re-map,
    # re-translate) re-derives from source WITHOUT re-pulling the catalog.
    # ================================================================
    source_system: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        comment="Feeder system that produced this row (e.g. 'artemis')"
    )
    source_id: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        comment="Source product id/GUID in the feeder system"
    )
    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Canonical source page — the 'View on Artemis' link (§9.6); doubles as a price-parity check"
    )
    source_lang: Mapped[str | None] = mapped_column(
        String(8),
        nullable=True,
        comment="Language the source text was pulled in (en primary; de/fr/it skins live in translations)"
    )
    artemis_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Full source breadcrumb verbatim (lossless) — recovers the deep tree for a future categories table"
    )
    needs_translation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if the primary text is missing a language skin and the LLM layer should fill it"
    )

    # §6a Rich-metadata bag (normalized, queryable keys: brand/material/size/...) +
    # the verbatim source facets kept losslessly alongside it.
    attributes: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="§6a normalized rich-metadata bag (brand, material, size, count, ...) — queryable"
    )
    raw_facets: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Verbatim source spec facets (lossless — never normalized/discarded)"
    )

    # Enrichment metadata (confidence per axis, flags, and which brain/recipe produced it).
    enrichment_confidence: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Per-axis confidence {category, class, description}"
    )
    enrichment_flags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Review flags list (needs_review, needs_description, needs_translation, ...)"
    )
    enrichment_meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Provenance of the enrichment run {model, recipe_version, run_id}"
    )

    # §6c SHARE rail: a Banco-owned permalink to this item online — the QR target on the
    # printed catalog / peelable sticker (separate from the La Piazza listing slug above).
    qr_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Banco-owned permalink for the item's QR (SHARE rail — postcard / La Piazza on-ramp)"
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
    translations: Mapped[list["ProductTranslationModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductTranslationModel.lang",
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


class ProductTranslationModel(Base):
    """
    Per-language text "skin" for a product (§6d multilingual layer).

    A product = ONE language-independent CORE (price, EAN, QR, photo, behaviour-class,
    age-flag, attribute *values*) + N text skins. Only name/description/labels change
    per language. The core lives on ProductModel; each (product, lang) skin lives here.

    Provenance matters: `provenance='source'` = real text pulled from the feeder
    (Artemis DE/FR are free fetches); `provenance='machine'` = AI-translated (IT and
    German stragglers), flagged so you always know which German is the *real* German.
    Display picks the customer's lang, falls back to EN if a skin is missing.

    WHY A TABLE (not name_i18n JSON columns): per-language provenance + needs_review is
    relational state that queries cleanly ("all machine FR awaiting review" = one WHERE);
    adding IT or back-filling a gap = UPSERT one row (deltas-aware) without rewriting the
    hot product row or the other languages' text.
    """
    __tablename__ = 'product_translations'
    __table_args__ = (
        UniqueConstraint('product_id', 'lang', name='uq_product_translations_product_lang'),
    )

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
    lang: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="BCP-47-ish language code: en (primary) / de / fr / it",
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Product name in this language",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Product description in this language",
    )
    provenance: Mapped[str] = mapped_column(
        String(16),
        default="source",
        nullable=False,
        comment="'source' = real feeder text | 'machine' = AI-translated",
    )
    needs_review: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True for machine translations awaiting human sign-off",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="translations")

    def __repr__(self):
        return f"<ProductTranslationModel(product_id='{self.product_id}', lang='{self.lang}')>"
