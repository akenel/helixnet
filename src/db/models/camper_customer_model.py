# File: src/db/models/camper_customer_model.py
"""
CamperCustomerModel - Customer profiles for Camper & Tour, Trapani.
Simplified from the CRACK model -- just contact info + visit history.

"The postcard is the handshake. The coffee is the close."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Text, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class CustomerLanguage(str, enum.Enum):
    """Preferred language -- Sicily is multilingual tourist territory"""
    IT = "it"
    EN = "en"
    DE = "de"
    FR = "fr"


class CamperCustomerModel(Base):
    """
    A customer at Camper & Tour.
    Phone is the main lookup key -- Italians call, they don't email.
    """
    __tablename__ = 'camper_customers'

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

    # Preferences
    language: Mapped[CustomerLanguage] = mapped_column(
        SQLEnum(CustomerLanguage),
        default=CustomerLanguage.IT,
        nullable=False
    )

    # Tax ID (Italian codice fiscale or P.IVA for businesses)
    tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Codice Fiscale or P.IVA"
    )

    # Telegram notifications
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Telegram chat ID for bot notifications"
    )

    # Visit tracking
    first_visit: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_visit: Mapped[date | None] = mapped_column(Date, nullable=True)
    visit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )

    # Preferences
    preferred_contact_method: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="phone, whatsapp, email, telegram -- how they want to hear from us"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="General notes visible to all"
    )
    internal_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Staff-only: 'pays cash', 'morning guy', 'picky about paint matching'"
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
    vehicles: Mapped[list["CamperVehicleModel"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    service_jobs: Mapped[list["CamperServiceJobModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CamperCustomer(name='{self.name}', phone='{self.phone}')>"
