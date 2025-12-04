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


# ================================================================
# ZONES - Front vs Back (Michel's Lab)
# ================================================================

class WashZone(enum.Enum):
    """Wash station zones"""
    FRONT_CATS = "front_cats"           # Cats - anyone can do
    FRONT_SMALL_DOGS = "front_small"    # Small dogs - trained staff
    FRONT_BIRDS = "front_birds"         # Birds - gentle touch
    BACK_LAB = "back_lab"               # Michel's domain - BIG DOGS, training, experiments
    BACK_HUSKY = "back_husky"           # Husky/Giant breeds - Gerry territory


class GroomerSkill(enum.Enum):
    """What each groomer can handle"""
    CATS_BASIC = "cats_basic"
    CATS_ADVANCED = "cats_advanced"
    DOGS_SMALL = "dogs_small"
    DOGS_MEDIUM = "dogs_medium"
    DOGS_LARGE = "dogs_large"           # Requires training
    DOGS_GIANT = "dogs_giant"           # Gerry/Michel only
    BIRDS = "birds"
    EXOTIC = "exotic"                   # Michel only
    YOUTUBE_CERTIFIED = "youtube_cert"  # Andy's emergency mode


class CameraStatus(enum.Enum):
    """Camera feed status"""
    OFFLINE = "offline"
    RECORDING = "recording"
    LIVE = "live"
    PROCESSING = "processing"


class MediaStatus(enum.Enum):
    """Media processing status"""
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    PURCHASED = "purchased"
    EXPIRED = "expired"


# ================================================================
# GROOMER MODEL - Michel, Andy, Gerry
# ================================================================

class GroomerModel(Base):
    """
    The team. Michel the master. Gerry the cat guy. Andy the floater.

    "You can not technically leave that nut alone in any bathroom"
    - Angel, on Michel, 2025
    """
    __tablename__ = 'groomers'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Groomer name"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="The Dr. Suess name"
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="Phone (if they answer it)"
    )

    # Skills - what they can handle
    can_do_cats: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_small_dogs: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_medium_dogs: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_large_dogs: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_giant_dogs: Mapped[bool] = mapped_column(Boolean, default=False)  # Husky territory
    can_do_birds: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_exotic: Mapped[bool] = mapped_column(Boolean, default=False)
    youtube_certified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Watched the videos. Emergency mode."
    )

    # Zone access
    allowed_zones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated zones: front_cats,front_small,back_lab"
    )

    # Behavior flags
    answers_phone: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="False for Michel"
    )
    needs_supervision: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="True for Michel - cameras on at all times"
    )
    is_on_call: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Can be summoned by signal"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<GroomerModel(name='{self.name}', cats={self.can_do_cats}, dogs_giant={self.can_do_giant_dogs})>"


# ================================================================
# WASH STATION - With Cameras
# ================================================================

class WashStationModel(Base):
    """
    Wash stations with camera feeds.

    "Cameras even up Michel's ass so at the end PUSS and them
    can watch it and if Michel can do it they know how the master
    did it - no HOCUS POCUS" - Angel, 2025

    Like roller coasters - the ride is one thing,
    but the PHOTO at the end is the real business.
    """
    __tablename__ = 'wash_stations'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Station Identity
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="Station name: TUB_1, TUB_2, GROOMING_TABLE"
    )
    zone: Mapped[WashZone] = mapped_column(
        SQLEnum(WashZone),
        nullable=False,
        comment="Which zone this station is in"
    )

    # Capabilities
    can_handle_species: Mapped[str] = mapped_column(
        String(200),
        default="dog,cat",
        comment="Comma-separated: dog,cat,bird"
    )
    max_pet_size: Mapped[PetSize] = mapped_column(
        SQLEnum(PetSize),
        default=PetSize.MEDIUM,
        comment="Largest pet this station can handle"
    )
    has_dryer: Mapped[bool] = mapped_column(Boolean, default=True)
    has_grooming_table: Mapped[bool] = mapped_column(Boolean, default=False)

    # Camera Setup - THE MONEY MAKER
    has_camera: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Station has camera for recording"
    )
    camera_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="RTSP or stream URL"
    )
    camera_status: Mapped[CameraStatus] = mapped_column(
        SQLEnum(CameraStatus),
        default=CameraStatus.OFFLINE
    )

    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    current_appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Currently in use by this appointment"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<WashStationModel(name='{self.name}', zone='{self.zone.value}', camera={self.has_camera})>"


# ================================================================
# PET MEDIA SESSION - The Roller Coaster Photo Model
# ================================================================

class PetMediaSession(Base):
    """
    Media capture for each wash session.

    Like roller coasters - the ride is the service,
    but the PHOTO/VIDEO is where the money is.

    "Remember the roller coasters - no money there
    but the pics after the show - have can we take it now,
    no WAIT needs another 30 seconds for polaroids to dry,
    don't SHAKE it YET" - Angel, 2025
    """
    __tablename__ = 'pet_media_sessions'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Links
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('pet_wash_appointments.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('pets.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    station_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('wash_stations.id', ondelete='SET NULL'),
        nullable=True
    )
    groomer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('groomers.id', ondelete='SET NULL'),
        nullable=True,
        comment="Who did the work (Michel, Gerry, etc)"
    )

    # Recording Times
    recording_started: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    recording_ended: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Media Files - The Polaroids
    video_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Full session video URL"
    )
    video_thumbnail_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Video thumbnail"
    )
    photo_before_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Before photo - the scruffy arrival"
    )
    photo_after_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="After photo - the glamour shot"
    )
    photo_action_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Mid-wash action shot"
    )

    # Processing Status
    status: Mapped[MediaStatus] = mapped_column(
        SQLEnum(MediaStatus),
        default=MediaStatus.RECORDING
    )
    processing_progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="0-100 processing percentage"
    )

    # Preview - Free teaser like roller coaster screens
    preview_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Free preview - low res with watermark"
    )

    # Expiry - Don't shake it yet, but also don't wait forever
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Media expires after X days if not purchased"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<PetMediaSession(pet_id='{self.pet_id}', status='{self.status.value}')>"


# ================================================================
# MEDIA PURCHASE - When They Buy the Polaroid
# ================================================================

class MediaPurchase(Base):
    """
    When the customer buys their pet's spa day content.

    The roller coaster photo booth model:
    - Service = ride ticket
    - Photos/Video = where the real margin is
    """
    __tablename__ = 'media_purchases'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Links
    media_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('pet_media_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id', ondelete='SET NULL'),
        nullable=True
    )

    # What they bought
    includes_video: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_photos: Mapped[bool] = mapped_column(Boolean, default=True)
    includes_before_after: Mapped[bool] = mapped_column(Boolean, default=True)

    # Pricing
    price_chf: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price paid"
    )
    paid: Mapped[bool] = mapped_column(Boolean, default=False)

    # Delivery
    download_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Full quality download link"
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="How many times downloaded"
    )
    emailed_to: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Sent to this email"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<MediaPurchase(session='{self.media_session_id}', price={self.price_chf})>"


# ================================================================
# MEDIA PRICING - The Photo Booth Menu
# ================================================================
MEDIA_PRICING = {
    "photo_pack": 15.00,        # Before + After + Action shot
    "video_clip": 25.00,        # 2-minute highlight reel
    "full_video": 45.00,        # Full session recording
    "deluxe_pack": 55.00,       # Everything - photos + full video
    "digital_frame": 10.00,     # Just the glamour shot, high res
}


# ================================================================
# DEFAULT GROOMERS - The Starting Lineup
# ================================================================
DEFAULT_GROOMERS = [
    {
        "name": "Michel",
        "nickname": "The Lorax",
        "can_do_cats": True,
        "can_do_small_dogs": True,
        "can_do_medium_dogs": True,
        "can_do_large_dogs": True,
        "can_do_giant_dogs": True,
        "can_do_birds": True,
        "can_do_exotic": True,
        "youtube_certified": False,  # Doesn't need it
        "allowed_zones": "front_cats,front_small,front_birds,back_lab,back_husky",
        "answers_phone": False,  # NEVER
        "needs_supervision": True,  # Cameras on at all times
        "is_on_call": True,
    },
    {
        "name": "Gerry",
        "nickname": "The Smart Mouse",
        "can_do_cats": True,
        "can_do_small_dogs": False,
        "can_do_medium_dogs": False,
        "can_do_large_dogs": True,  # Trained by Michel
        "can_do_giant_dogs": True,  # The Husky guy
        "can_do_birds": False,
        "can_do_exotic": False,
        "youtube_certified": False,
        "allowed_zones": "front_cats,back_lab,back_husky",
        "answers_phone": True,
        "needs_supervision": False,
        "is_on_call": False,
    },
    {
        "name": "Andy",
        "nickname": "Angel Wings",
        "can_do_cats": True,  # YouTube certified
        "can_do_small_dogs": True,  # YouTube certified
        "can_do_medium_dogs": False,
        "can_do_large_dogs": False,
        "can_do_giant_dogs": False,
        "can_do_birds": False,
        "can_do_exotic": False,
        "youtube_certified": True,  # Emergency mode
        "allowed_zones": "front_cats,front_small",
        "answers_phone": True,
        "needs_supervision": False,
        "is_on_call": False,
    },
]


# ================================================================
# DEFAULT WASH STATIONS
# ================================================================
DEFAULT_STATIONS = [
    {
        "name": "TUB_1",
        "zone": WashZone.FRONT_CATS,
        "can_handle_species": "cat",
        "max_pet_size": PetSize.SMALL,
        "has_camera": True,
    },
    {
        "name": "TUB_2",
        "zone": WashZone.FRONT_SMALL_DOGS,
        "can_handle_species": "dog,cat",
        "max_pet_size": PetSize.MEDIUM,
        "has_camera": True,
    },
    {
        "name": "BIRD_STATION",
        "zone": WashZone.FRONT_BIRDS,
        "can_handle_species": "bird",
        "max_pet_size": PetSize.TINY,
        "has_camera": True,
    },
    {
        "name": "MICHEL_LAB",
        "zone": WashZone.BACK_LAB,
        "can_handle_species": "dog,cat,bird,rabbit,reptile,other",
        "max_pet_size": PetSize.LARGE,
        "has_camera": True,  # Cameras ALWAYS on Michel
        "has_grooming_table": True,
    },
    {
        "name": "HUSKY_TUB",
        "zone": WashZone.BACK_HUSKY,
        "can_handle_species": "dog",
        "max_pet_size": PetSize.GIANT,
        "has_camera": True,
        "has_dryer": True,
    },
]
