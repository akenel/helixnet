# File: src/db/models/camper_supplier_model.py
"""
CamperSupplierModel - Supplier directory for Camper & Tour, Trapani.
Mix of regular suppliers (AutoParts Trapani) and ad-hoc (that guy in Palermo).

"System should flag if not in stock or external provider" -- Angel
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CamperSupplierModel(Base):
    """
    A supplier in the Camper & Tour directory.
    Separate from the Swiss SupplierModel -- this is Trapani territory.
    """
    __tablename__ = 'camper_suppliers'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Supplier name: 'AutoParts Trapani', 'Palermo Seals'"
    )
    contact_person: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Main contact: 'Giuseppe'"
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
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

    specialty: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="e.g., 'Seals & gaskets', 'Electrical', 'Paint & bodywork'"
    )
    lead_time_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Typical delivery time in business days"
    )

    is_preferred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Regular/preferred supplier vs ad-hoc"
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
        return f"<CamperSupplier(name='{self.name}'{pref})>"
