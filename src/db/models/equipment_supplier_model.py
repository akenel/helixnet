# File: src/db/models/equipment_supplier_model.py
"""
EquipmentSupplierModel - Where equipment comes from.
Alibaba, COOLIE Japan, Borris Custom.

"3 months to find BLQ quality. 500 PowerPoint slides." - SAL about COOLIE
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Numeric, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class SupplierType(str, enum.Enum):
    """What kind of supplier"""
    MANUFACTURER = "manufacturer"
    DISTRIBUTOR = "distributor"
    FABRICATOR = "fabricator"
    PARTS = "parts"
    SERVICE = "service"
    REFURB = "refurb"


class EquipmentSupplierModel(Base):
    """
    A supplier in the network.
    Alibaba, COOLIE Japan, Borris Custom, etc.
    """
    __tablename__ = 'equipment_suppliers'

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
        nullable=False
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Short code (e.g., ALI, COOLIE, BORRIS)"
    )
    supplier_type: Mapped[SupplierType] = mapped_column(
        SQLEnum(SupplierType),
        nullable=False
    )

    # Location
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Contact
    contact_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Business
    website: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )
    payment_terms: Mapped[str] = mapped_column(
        String(50),
        default="Net 30",
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False
    )

    # Logistics
    typical_lead_time_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False
    )
    ships_via: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated shipping methods"
    )

    # Quality
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    quality_rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="1-5 stars"
    )

    # Specialties
    specialties: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated specialties"
    )

    # Stats
    total_orders: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_spent: Mapped[float] = mapped_column(
        Numeric(14, 2),
        default=0,
        nullable=False
    )
    on_time_rate: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
        comment="Percentage of on-time deliveries"
    )

    # Network connection
    referred_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who referred this supplier (e.g., COOLIE, YUKI)"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    equipment: Mapped[list["EquipmentModel"]] = relationship(
        back_populates="supplier"
    )
    purchase_orders: Mapped[list["PurchaseOrderModel"]] = relationship(
        back_populates="supplier"
    )

    def __repr__(self):
        return f"<EquipmentSupplierModel(code='{self.code}', name='{self.name}', country='{self.country}')>"
