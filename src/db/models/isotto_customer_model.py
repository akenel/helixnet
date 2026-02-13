# File: src/db/models/isotto_customer_model.py
"""
IsottoCustomerModel - Customer profiles for ISOTTO Sport Print Shop, Trapani.
Since 1968. Famous Guy knows his stuff.

"The postcard is the handshake. The coffee is the close."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Text, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class IsottoCustomerModel(Base):
    """
    A customer at ISOTTO Sport Print Shop.
    Phone is the main lookup key -- Italians call, they don't email.
    """
    __tablename__ = 'isotto_customers'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Full name"
    )
    company_name: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        comment="Business name (ragione sociale)"
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        index=True,
        nullable=True,
        comment="Phone number -- the fast lookup key"
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Tax ID (Italian codice fiscale or P.IVA for businesses)
    tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Codice Fiscale or P.IVA"
    )

    # Order tracking
    first_order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    # Notes
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
    orders: Mapped[list["IsottoOrderModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<IsottoCustomer(name='{self.name}', company='{self.company_name}', phone='{self.phone}')>"
