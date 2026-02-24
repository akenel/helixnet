# File: src/db/models/isotto_supplier_model.py
"""
IsottoSupplierModel - Supplier directory for ISOTTO Sport, Trapani.
ROLY, Fruit of the Loom, etc. -- the blank merchandise sources.

Since 1968. Famous Guy knows his suppliers.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IsottoSupplierModel(Base):
    """
    A merchandise supplier in the ISOTTO Sport directory.
    Tracks blank garment/product sources for the print shop.
    """
    __tablename__ = 'isotto_suppliers'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="Supplier name: 'ROLY', 'Fruit of the Loom'"
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="Short code: 'ROLY', 'FOTL'"
    )
    contact_person: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Main contact person"
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    default_lead_time_days: Mapped[int] = mapped_column(
        Integer,
        default=14,
        nullable=False,
        comment="Typical delivery time in business days"
    )
    min_order_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Minimum order amount in EUR"
    )

    is_preferred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Preferred/regular supplier"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    def __repr__(self):
        pref = " [PREFERRED]" if self.is_preferred else ""
        return f"<IsottoSupplier(name='{self.name}', code='{self.code}'{pref})>"
