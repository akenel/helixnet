# File: src/db/models/shipment_model.py
"""
ShipmentModel - How equipment travels. Containers, pallets, parcels.
Charlie & YUKI ride the 20ft container from Yokohama to Rotterdam.

"We ride WITH the equipment." - YUKI
"""
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class ShipmentType(str, enum.Enum):
    """How it travels"""
    # Small
    PARCEL = "parcel"
    PALLET = "pallet"

    # Medium
    MULTI_PALLET = "multi_pallet"
    LTL = "ltl"
    FTL = "ftl"

    # Large (containers)
    CONTAINER_10FT = "container_10ft"
    CONTAINER_20FT = "container_20ft"
    CONTAINER_40FT = "container_40ft"
    CONTAINER_40FT_HC = "container_40ft_hc"

    # Special
    AIR_FREIGHT = "air_freight"
    HAND_CARRY = "hand_carry"


class ShipmentStatus(str, enum.Enum):
    """Where is the shipment"""
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT_LAND = "in_transit_land"
    IN_TRANSIT_SEA = "in_transit_sea"
    IN_TRANSIT_AIR = "in_transit_air"
    AT_ORIGIN_PORT = "at_origin_port"
    AT_DESTINATION_PORT = "at_destination_port"
    CUSTOMS_PENDING = "customs_pending"
    CUSTOMS_INSPECTION = "customs_inspection"
    CUSTOMS_CLEARED = "customs_cleared"
    CUSTOMS_HELD = "customs_held"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RECEIVED = "received"


class ShipmentModel(Base):
    """
    A shipment from supplier to destination.
    Charlie & YUKI ride the 20ft container.
    """
    __tablename__ = 'shipments'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    shipment_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="e.g., SHIP-2025-YC-047"
    )

    # Type
    shipment_type: Mapped[ShipmentType] = mapped_column(
        SQLEnum(ShipmentType),
        nullable=False
    )

    # Container details
    container_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="e.g., MSCU-7749-COOLIE"
    )
    container_size: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="20ft, 40ft, etc."
    )
    seal_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Carrier
    carrier_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Maersk, DHL, etc."
    )
    carrier_tracking: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    vessel_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Ship name (e.g., MSC AURORA)"
    )
    voyage_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Route - Origin
    origin_country: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_city: Mapped[str] = mapped_column(String(100), nullable=False)
    origin_port: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., Yokohama"
    )

    # Route - Destination
    destination_country: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_port: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., Rotterdam"
    )
    final_destination: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="e.g., Zurich warehouse"
    )
    final_destination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    # Status
    status: Mapped[ShipmentStatus] = mapped_column(
        SQLEnum(ShipmentStatus),
        default=ShipmentStatus.PENDING,
        nullable=False
    )

    # Contents
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('purchase_orders.id'),
        nullable=True
    )
    total_pieces: Mapped[int] = mapped_column(Integer, default=0)
    total_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume_cbm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Cubic meters"
    )

    # Value
    declared_value: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="USD",
        nullable=False
    )

    # Dates
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    eta_port: Mapped[date | None] = mapped_column(Date, nullable=True)
    eta_destination: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_arrival_port: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_arrival_destination: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Customs
    requires_customs: Mapped[bool] = mapped_column(Boolean, default=True)
    customs_clearance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customs_clearances.id'),
        nullable=True
    )

    # Special cargo
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature_controlled: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature_range: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="e.g., 2-8C"
    )

    # Insurance
    is_insured: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_value: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    # Delays
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False)
    delay_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    delay_days: Mapped[int] = mapped_column(Integer, default=0)

    # The human element
    handled_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who's managing this shipment (e.g., YUKI)"
    )
    passengers: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated names (e.g., CHARLIE) - hidden in container, shhh"
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
    purchase_orders: Mapped["PurchaseOrderModel"] = relationship(back_populates="shipments")
    customs_clearance: Mapped["CustomsClearanceModel"] = relationship(
        back_populates="shipments",
        foreign_keys="[ShipmentModel.customs_clearance_id]"
    )

    def __repr__(self):
        return f"<ShipmentModel(num='{self.shipment_number}', type={self.shipment_type}, status={self.status})>"
