# File: src/db/models/reference_product_model.py
"""
ReferenceProductModel — the REFERENCE CATALOG (product master) for Banco POS. (BL-97)

This is NOT the live catalog and NOT inventory. It is a large, canonical, supplier-fed
lookup list (the full 420 / TMR dump — tens of thousands of items, with real title,
description and photo). The POS searches it but NEVER sells from it directly.

When a cashier scans/searches an item that isn't in the live `products` catalog but IS in
here, they "adopt" it: one tap copies the real title/description/photo into a live product
(see POST /api/v1/pos/reference/{id}/adopt). The cashier confirms the price; they never
re-type or invent a name. Zero-perpetual-inventory is unchanged — this is purely a
copy-the-right-data-in helper, a clipboard sitting beside the live catalog.

Written to only by the importer (scripts/import_reference_catalog.py); read-only at the
counter. Fed by periodic CSV dumps from the supplier.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Numeric, Text, UniqueConstraint, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ReferenceProductModel(Base):
    """A canonical supplier product record. Lookup-only; adopt into `products` to sell."""
    __tablename__ = 'reference_products'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Source + idempotency. `ref_key` is the stable per-supplier key the importer upserts on
    # (supplier_sku, else barcode, else a title slug) so re-importing a fresh dump updates in
    # place instead of duplicating.
    supplier: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Source supplier, e.g. '420' / 'TMR' — part of the upsert key",
    )
    ref_key: Mapped[str] = mapped_column(
        String(150), nullable=False,
        comment="Stable per-supplier key (supplier_sku|barcode|title-slug) for idempotent upsert",
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="The supplier's own article number, if any",
    )
    barcode: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True, comment="EAN/UPC from the dump, if present",
    )

    # The canonical data we copy on adopt — the whole point of the table.
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Canonical product name (becomes products.name)",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    suggested_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Supplier RRP — the cashier may override on adopt",
    )
    cost: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Supplier buy price, if present",
    )

    # BL-96: our skeleton mapping, set by scripts/reclassify_reference.py (re-runnable). Adopt
    # copies these onto the new product so a received item lands categorised + classed + age-gated.
    our_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    our_class: Mapped[str | None] = mapped_column(String(40), nullable=True)
    age_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # The original CSV row, kept verbatim for audit / future fields.
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint('supplier', 'ref_key', name='uq_reference_products_supplier_refkey'),
        # Trigram index for fast fuzzy title search (mirrors the live products search).
        Index('ix_reference_products_title_trgm', 'title',
              postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
    )

    def __repr__(self):
        return f"<ReferenceProductModel(supplier='{self.supplier}', title='{self.title}')>"
