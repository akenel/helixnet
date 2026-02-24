# File: src/db/models/isotto_artwork_model.py
"""
IsottoArtworkModel - Artwork files for ISOTTO Sport custom printing.
Logos, designs, team crests -- stored in MinIO, reusable across orders.

"The customer brings a logo on a USB stick. We scan it, upload it,
 and it's ready for every order from now on."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Numeric, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.db.models.isotto_catalog_model import IsottoPrintMethod

from .base import Base


class IsottoArtworkModel(Base):
    """
    An artwork file in the ISOTTO Sport library.
    Can be linked to a specific customer or order, or reusable across orders.
    """
    __tablename__ = 'isotto_artworks'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Optional links
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_customers.id'),
        nullable=True,
        index=True,
        comment="Owner customer (null = shop-owned artwork)"
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('isotto_orders.id'),
        nullable=True,
        index=True,
        comment="Specific order (null = reusable across orders)"
    )

    # Identity
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Artwork title: 'ASD Trapani Calcio Crest'"
    )

    # File storage (MinIO)
    file_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to source file (SVG, AI, PSD, PNG)"
    )
    thumbnail_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="MinIO path to thumbnail preview"
    )

    # Print specs
    print_method: Mapped[IsottoPrintMethod | None] = mapped_column(
        SQLEnum(IsottoPrintMethod, name='isotto_print_method', create_constraint=True,
                create_type=False),
        nullable=True,
        comment="Recommended print method for this artwork"
    )
    color_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of colors in the artwork"
    )
    width_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Artwork width in cm"
    )
    height_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        comment="Artwork height in cm"
    )

    # Flags
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Customer approved this artwork for production"
    )
    is_reusable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Can be used across multiple orders"
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    customer: Mapped["IsottoCustomerModel"] = relationship()
    order: Mapped["IsottoOrderModel"] = relationship()

    def __repr__(self):
        return f"<IsottoArtwork(title='{self.title}', approved={self.is_approved})>"
