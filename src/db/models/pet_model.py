# File: src/db/models/pet_model.py
"""
PetModel - Michel's Pet Wash Station
"Be water, my friend." - Bruce Lee
"Be furry, my friend." - Michel the Animal Whisperer

For the bookstore in Stans with the pet corner.
Where books meet barks. Where VIVI does therapy and Michel does magic.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


class PetSpecies(enum.Enum):
    """Pet species - Michel knows them all"""
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    HAMSTER = "hamster"
    GUINEA_PIG = "guinea_pig"
    FISH = "fish"
    REPTILE = "reptile"
    OTHER = "other"


class PetSize(enum.Enum):
    """Pet size for wash pricing"""
    TINY = "tiny"        # Under 5 kg
    SMALL = "small"      # 5-10 kg
    MEDIUM = "medium"    # 10-25 kg
    LARGE = "large"      # 25-40 kg
    GIANT = "giant"      # Over 40 kg


class WashServiceType(enum.Enum):
    """Wash services - Michel's menu"""
    BASIC_WASH = "basic_wash"           # Wash and dry
    FULL_GROOM = "full_groom"           # Wash, dry, trim
    NAIL_TRIM = "nail_trim"             # Just nails
    TEETH_CLEAN = "teeth_clean"         # Dental care
    FLEA_TREATMENT = "flea_treatment"   # Anti-flea
    DELUXE_SPA = "deluxe_spa"           # The works


class AppointmentStatus(enum.Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PetModel(Base):
    """
    Pet registry for HelixPETS.

    Michel knows every animal in Stans by name.
    Now Helix does too.
    """
    __tablename__ = 'pets'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Owner Link (to Customer when we have it)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Link to CustomerModel"
    )

    # Pet Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Pet name - Michel remembers them all"
    )
    species: Mapped[PetSpecies] = mapped_column(
        SQLEnum(PetSpecies),
        default=PetSpecies.DOG,
        nullable=False,
        comment="Pet species"
    )
    breed: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Breed if known"
    )
    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Fur/feather color"
    )
    size: Mapped[PetSize] = mapped_column(
        SQLEnum(PetSize),
        default=PetSize.MEDIUM,
        nullable=False,
        comment="Size category for pricing"
    )

    # Pet Details
    birth_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Birth date if known"
    )
    weight_kg: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Weight in kg"
    )
    microchip_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Microchip ID for identification"
    )

    # Health & Care Notes
    allergies: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Known allergies"
    )
    medical_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Medical conditions, vet notes"
    )
    temperament: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Friendly, nervous, aggressive, etc."
    )
    special_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Michel's notes - what makes this pet special"
    )

    # Owner Contact (backup if no customer_id)
    owner_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Owner name for quick lookup"
    )
    owner_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Owner phone"
    )

    # Photo
    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Pet photo URL"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active in system"
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
    appointments: Mapped[list["PetWashAppointment"]] = relationship(
        "PetWashAppointment",
        back_populates="pet",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<PetModel(name='{self.name}', species='{self.species.value}', owner='{self.owner_name}')>"


class PetWashAppointment(Base):
    """
    Pet wash appointments.
    Michel's calendar. The animal whisperer's schedule.
    """
    __tablename__ = 'pet_wash_appointments'

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Links
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('pets.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Appointment Details
    service_type: Mapped[WashServiceType] = mapped_column(
        SQLEnum(WashServiceType),
        default=WashServiceType.BASIC_WASH,
        nullable=False,
        comment="Type of service"
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Scheduled date/time"
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Expected duration"
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
        index=True
    )

    # Pricing
    price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Service price in CHF"
    )
    paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Appointment notes"
    )
    groomer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Michel's notes after service"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When service was completed"
    )

    # Relationships
    pet: Mapped["PetModel"] = relationship(
        "PetModel",
        back_populates="appointments"
    )

    def __repr__(self):
        return f"<PetWashAppointment(pet_id='{self.pet_id}', service='{self.service_type.value}', status='{self.status.value}')>"


# ================================================================
# PRICING - Michel's Rate Card
# ================================================================
WASH_PRICING = {
    # (service_type, size) -> price in CHF
    (WashServiceType.BASIC_WASH, PetSize.TINY): 15.00,
    (WashServiceType.BASIC_WASH, PetSize.SMALL): 20.00,
    (WashServiceType.BASIC_WASH, PetSize.MEDIUM): 30.00,
    (WashServiceType.BASIC_WASH, PetSize.LARGE): 40.00,
    (WashServiceType.BASIC_WASH, PetSize.GIANT): 55.00,

    (WashServiceType.FULL_GROOM, PetSize.TINY): 35.00,
    (WashServiceType.FULL_GROOM, PetSize.SMALL): 45.00,
    (WashServiceType.FULL_GROOM, PetSize.MEDIUM): 60.00,
    (WashServiceType.FULL_GROOM, PetSize.LARGE): 80.00,
    (WashServiceType.FULL_GROOM, PetSize.GIANT): 100.00,

    (WashServiceType.NAIL_TRIM, PetSize.TINY): 10.00,
    (WashServiceType.NAIL_TRIM, PetSize.SMALL): 12.00,
    (WashServiceType.NAIL_TRIM, PetSize.MEDIUM): 15.00,
    (WashServiceType.NAIL_TRIM, PetSize.LARGE): 18.00,
    (WashServiceType.NAIL_TRIM, PetSize.GIANT): 22.00,

    (WashServiceType.DELUXE_SPA, PetSize.TINY): 50.00,
    (WashServiceType.DELUXE_SPA, PetSize.SMALL): 65.00,
    (WashServiceType.DELUXE_SPA, PetSize.MEDIUM): 85.00,
    (WashServiceType.DELUXE_SPA, PetSize.LARGE): 110.00,
    (WashServiceType.DELUXE_SPA, PetSize.GIANT): 140.00,
}


def get_service_price(service_type: WashServiceType, size: PetSize) -> float:
    """Get price for a service based on pet size"""
    return WASH_PRICING.get((service_type, size), 30.00)  # Default price
