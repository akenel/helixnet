# File: src/db/models/isotto_order_model.py
"""
IsottoOrderModel - Print orders for ISOTTO Sport, Trapani.
The heart of the print shop: what was ordered, production status, and delivery.

Since 1968. Famous Guy knows his stuff.

"One shot, one kill. A QR code is a command."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class ProductType(str, enum.Enum):
    """What kind of print product"""
    POSTCARD = "postcard"
    BUSINESS_CARD = "business_card"
    FLYER = "flyer"
    BROCHURE = "brochure"
    BANNER = "banner"
    POSTER = "poster"
    TSHIRT = "tshirt"
    STICKER = "sticker"
    LABEL = "label"
    MENU = "menu"
    CUSTOM = "custom"


class OrderStatus(str, enum.Enum):
    """Order lifecycle: QUOTED -> APPROVED -> IN_PRODUCTION -> QUALITY_CHECK -> READY -> PICKED_UP -> INVOICED"""
    QUOTED = "quoted"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    QUALITY_CHECK = "quality_check"
    READY = "ready"
    PICKED_UP = "picked_up"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"


class ColorMode(str, enum.Enum):
    """Print color mode"""
    CMYK = "cmyk"
    BW = "bw"
    SPOT = "spot"


class DuplexMode(str, enum.Enum):
    """Duplex flip mode"""
    LONG_EDGE = "long_edge"
    SHORT_EDGE = "short_edge"


class Lamination(str, enum.Enum):
    """Lamination type"""
    NONE = "none"
    MATTE = "matte"
    GLOSSY = "glossy"


class IsottoOrderModel(Base):
    """
    A print order at ISOTTO Sport.
    Tracks the full lifecycle from quote to invoice.
    """
    __tablename__ = 'isotto_orders'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Order identity
    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
        comment="Sequential: ORD-20260213-0001"
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Short description: 'Pizza Planet 4-UP Postcards'"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the print job"
    )

    # Which customer
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_customers.id'),
        nullable=False,
        index=True
    )

    # Classification
    product_type: Mapped[ProductType] = mapped_column(
        SQLEnum(ProductType, name='isotto_product_type', create_constraint=True),
        nullable=False,
        default=ProductType.POSTCARD
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name='isotto_order_status', create_constraint=True),
        default=OrderStatus.QUOTED,
        nullable=False,
        index=True
    )

    # Pricing
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="EUR", nullable=False
    )

    # Print specifications
    paper_weight_gsm: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Paper weight in gsm (e.g., 250)"
    )
    color_mode: Mapped[ColorMode | None] = mapped_column(
        SQLEnum(ColorMode, name='isotto_color_mode', create_constraint=True),
        nullable=True,
        default=ColorMode.CMYK
    )
    duplex: Mapped[bool] = mapped_column(Boolean, default=False)
    duplex_mode: Mapped[DuplexMode | None] = mapped_column(
        SQLEnum(DuplexMode, name='isotto_duplex_mode', create_constraint=True),
        nullable=True
    )
    lamination: Mapped[Lamination | None] = mapped_column(
        SQLEnum(Lamination, name='isotto_lamination', create_constraint=True),
        nullable=True,
        default=Lamination.NONE
    )
    size_description: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., 'A4 landscape', '210x99mm'"
    )
    copies_per_sheet: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="e.g., 4 for 4-UP"
    )
    cutting_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cutting instructions for the cutter machine"
    )
    finishing_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional finishing instructions"
    )

    # Files
    artwork_files: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated paths/URLs to artwork files"
    )
    proof_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    proof_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Production tracking
    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Operator name"
    )
    estimated_completion: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timeline
    quoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    production_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    picked_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notes
    customer_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="What the customer requested"
    )
    production_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Internal production observations"
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
    customer: Mapped["IsottoCustomerModel"] = relationship(back_populates="orders")

    def __repr__(self):
        return f"<IsottoOrder(number='{self.order_number}', title='{self.title}', status={self.status})>"
