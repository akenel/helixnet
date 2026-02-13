# File: src/db/models/camper_vehicle_model.py
"""
CamperVehicleModel - Vehicle records for Camper & Tour, Trapani.
Motorhomes, caravans, campervans -- what rolls into Sebastino's shop.

"Casa e dove parcheggi." - Home is where you park it.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class VehicleType(str, enum.Enum):
    """What kind of vehicle"""
    MOTORHOME = "motorhome"
    CARAVAN = "caravan"
    CAMPERVAN = "campervan"
    VAN = "van"
    TRAILER = "trailer"
    OTHER = "other"


class VehicleStatus(str, enum.Enum):
    """Where is this vehicle in the service lifecycle"""
    CHECKED_IN = "checked_in"
    IN_SERVICE = "in_service"
    WAITING_PARTS = "waiting_parts"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"


class CamperVehicleModel(Base):
    """
    A vehicle registered at Camper & Tour.
    The plate number is the fast lookup key -- customer arrives,
    type the plate, see full history.
    """
    __tablename__ = 'camper_vehicles'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    registration_plate: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="License plate -- the fast lookup key"
    )
    chassis_number: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="VIN / chassis number"
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SQLEnum(VehicleType, name='camper_vehicle_type', create_constraint=True),
        nullable=False,
        default=VehicleType.CAMPERVAN
    )
    make: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., Fiat, Mercedes, VW"
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., Ducato, Sprinter, California"
    )
    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Dimensions
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Owner (denormalized for quick display -- FK is optional)
    owner_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Denormalized owner name for display"
    )
    owner_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    owner_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('camper_customers.id'),
        nullable=True,
        comment="FK to customer profile (nullable -- walk-ins)"
    )

    # Insurance
    insurance_company: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    insurance_policy: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Status
    status: Mapped[VehicleStatus] = mapped_column(
        SQLEnum(VehicleStatus, name='camper_vehicle_status', create_constraint=True),
        default=VehicleStatus.PICKED_UP,
        nullable=False
    )

    # Documentation
    photos: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated photo URLs"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Active flag
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
    owner: Mapped["CamperCustomerModel"] = relationship(
        back_populates="vehicles",
        foreign_keys=[owner_id]
    )
    service_jobs: Mapped[list["CamperServiceJobModel"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CamperVehicle(plate='{self.registration_plate}', type={self.vehicle_type}, status={self.status})>"
