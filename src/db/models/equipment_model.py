# File: src/db/models/equipment_model.py
"""
EquipmentModel - The machines. Salad bars, coffee stations, milking machines.
YUKI & CHARLIE's domain. What gets shipped in containers.

"I have the machines." - Marco
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Integer, Boolean, Text, Numeric, Float, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class EquipmentType(str, enum.Enum):
    """What kind of equipment"""
    # Food service
    SALAD_BAR = "salad_bar"
    FRIDGE_BAR = "fridge_bar"
    COFFEE_STATION = "coffee_station"
    VENDING_MACHINE = "vending_machine"

    # Kitchen
    PREP_TABLE = "prep_table"
    PIZZA_OVEN = "pizza_oven"
    MIXER = "mixer"
    SLICER = "slicer"

    # Farm
    MILKING_MACHINE = "milking_machine"
    IRRIGATION = "irrigation"
    GREENHOUSE = "greenhouse"
    COMPOST_SYSTEM = "compost_system"

    # Storage
    WALK_IN_FRIDGE = "walk_in_fridge"
    FREEZER = "freezer"
    LOCKER_UNIT = "locker_unit"

    # Lab
    LAB_EQUIPMENT = "lab_equipment"

    # Cleaning
    ROBOT_CLEANER = "robot_cleaner"
    DISHWASHER = "dishwasher"

    # Other
    JUKEBOX = "jukebox"
    CUSTOM = "custom"


class EquipmentStatus(str, enum.Enum):
    """Where is it in the lifecycle"""
    # Pre-arrival
    PLANNED = "planned"
    ORDERED = "ordered"
    MANUFACTURING = "manufacturing"
    READY_TO_SHIP = "ready_to_ship"

    # In transit
    IN_TRANSIT = "in_transit"
    AT_PORT = "at_port"
    CUSTOMS_HOLD = "customs_hold"
    CUSTOMS_CLEARED = "customs_cleared"

    # Post-arrival
    IN_WAREHOUSE = "in_warehouse"
    ASSEMBLING = "assembling"
    TESTING = "testing"
    READY_TO_INSTALL = "ready_to_install"

    # Installed
    INSTALLING = "installing"
    INSTALLED = "installed"
    OPERATIONAL = "operational"

    # Maintenance
    NEEDS_MAINTENANCE = "needs_maintenance"
    UNDER_REPAIR = "under_repair"
    WAITING_PARTS = "waiting_parts"

    # End of life
    DECOMMISSIONED = "decommissioned"
    SOLD = "sold"
    SCRAPPED = "scrapped"


class EquipmentModel(Base):
    """
    A piece of equipment in the network.
    Salad bar, coffee machine, milking machine, etc.
    """
    __tablename__ = 'equipment'

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
    equipment_type: Mapped[EquipmentType] = mapped_column(
        SQLEnum(EquipmentType),
        nullable=False
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True
    )
    model_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Source
    equipment_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('equipment_suppliers.id'),
        nullable=True
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('purchase_orders.id'),
        nullable=True
    )

    # Status
    status: Mapped[EquipmentStatus] = mapped_column(
        SQLEnum(EquipmentStatus),
        default=EquipmentStatus.PLANNED,
        nullable=False
    )

    # Location
    current_location_type: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
        nullable=False
    )
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    current_location_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # Installation
    installed_at_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Which bar/farm is it installed at"
    )
    installed_at_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    installed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    installed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who installed it (e.g., Marco)"
    )

    # Specs
    dimensions: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., 200x80x120 cm"
    )
    weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    power_requirements: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., 220V, 16A"
    )
    capacity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g., 50 salads/hour"
    )

    # Value
    purchase_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        default="CHF",
        nullable=False
    )
    warranty_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # Maintenance
    last_maintenance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    next_maintenance_due: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    maintenance_interval_days: Mapped[int] = mapped_column(
        Integer,
        default=90,
        nullable=False
    )
    total_maintenance_events: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    total_downtime_hours: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    # Documentation
    manual_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Custom (Borris specials)
    is_custom: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    custom_specs: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
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
    supplier: Mapped["EquipmentSupplierModel"] = relationship(back_populates="equipment")
    purchase_order: Mapped["PurchaseOrderModel"] = relationship(back_populates="equipment")
    maintenance_events: Mapped[list["MaintenanceEventModel"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<EquipmentModel(name='{self.name}', type={self.equipment_type}, status={self.status})>"
