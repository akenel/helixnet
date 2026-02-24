# File: src/db/models/isotto_catalog_model.py
"""
IsottoCatalogProductModel - Product catalog for ISOTTO Sport custom merch.
Each product = a blank garment/item from a supplier that ISOTTO can print on.

T-shirts, polos, hoodies, caps, mugs, bags -- all the merch.
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.core.constants import HelixEnum

from .base import Base


class IsottoMerchCategory(HelixEnum):
    """Merchandise category"""
    TSHIRT = "tshirt"
    POLO = "polo"
    HOODIE = "hoodie"
    JACKET = "jacket"
    CAP = "cap"
    BAG = "bag"
    MUG = "mug"
    APRON = "apron"
    VEST = "vest"
    ACCESSORY = "accessory"
    CUSTOM = "custom"


class IsottoPrintMethod(HelixEnum):
    """Available print/decoration methods"""
    SCREEN_PRINT = "screen_print"
    DTG = "dtg"
    EMBROIDERY = "embroidery"
    VINYL = "vinyl"
    SUBLIMATION = "sublimation"
    TRANSFER = "transfer"


class IsottoCatalogProductModel(Base):
    """
    A product in the ISOTTO Sport catalog.
    Represents a blank garment/item that can be customized with printing.
    """
    __tablename__ = 'isotto_catalog_products'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Supplier link
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_suppliers.id'),
        nullable=False,
        index=True
    )
    supplier_product_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Supplier's product code, e.g. ROLY '6502'"
    )

    # Product identity
    name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
        comment="Product name: 'ROLY Bahrain T-Shirt'"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    category: Mapped[IsottoMerchCategory] = mapped_column(
        SQLEnum(IsottoMerchCategory, name='isotto_merch_category', create_constraint=True),
        nullable=False,
        index=True
    )

    # Available options (JSONB arrays)
    available_colors: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment='["white","black","navy","red"]'
    )
    available_sizes: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment='["XS","S","M","L","XL","XXL","3XL"]'
    )

    # Pricing
    supplier_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="What ISOTTO pays per blank"
    )
    retail_base_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Base price to customer"
    )
    personalization_markup: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("5.00"),
        nullable=False,
        comment="EUR extra per personalized item"
    )

    # Print specs
    print_areas: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment='[{"area":"front","max_width_cm":30,"max_height_cm":40}]'
    )
    recommended_print_methods: Mapped[list | None] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment='["screen_print","dtg"]'
    )

    # Logistics
    lead_time_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Override supplier default lead time"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path or URL to product image"
    )
    has_sample_in_store: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Display sample available at ISOTTO?"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    tags: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated tags for search"
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
    supplier: Mapped["IsottoSupplierModel"] = relationship()
    stock_entries: Mapped[list["IsottoCatalogStockModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<IsottoCatalogProduct(name='{self.name}', category={self.category})>"
