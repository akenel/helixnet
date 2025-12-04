# File: src/schemas/pet_schema.py
"""
Pydantic schemas for HelixPETS.
Michel's pet wash station. Where furry friends get the spa treatment.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


class PetSpeciesEnum(str, Enum):
    """Pet species"""
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    HAMSTER = "hamster"
    GUINEA_PIG = "guinea_pig"
    FISH = "fish"
    REPTILE = "reptile"
    OTHER = "other"


class PetSizeEnum(str, Enum):
    """Pet size for pricing"""
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    GIANT = "giant"


class WashServiceTypeEnum(str, Enum):
    """Wash service types"""
    BASIC_WASH = "basic_wash"
    FULL_GROOM = "full_groom"
    NAIL_TRIM = "nail_trim"
    TEETH_CLEAN = "teeth_clean"
    FLEA_TREATMENT = "flea_treatment"
    DELUXE_SPA = "deluxe_spa"


class AppointmentStatusEnum(str, Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


# ================================================================
# PET SCHEMAS
# ================================================================

class PetBase(BaseModel):
    """Base pet fields"""
    name: str = Field(..., max_length=100, description="Pet name")
    species: PetSpeciesEnum = Field(default=PetSpeciesEnum.DOG, description="Species")
    breed: Optional[str] = Field(None, max_length=100, description="Breed")
    color: Optional[str] = Field(None, max_length=50, description="Color")
    size: PetSizeEnum = Field(default=PetSizeEnum.MEDIUM, description="Size category")
    birth_date: Optional[datetime] = Field(None, description="Birth date")
    weight_kg: Optional[float] = Field(None, ge=0, le=200, description="Weight in kg")
    microchip_id: Optional[str] = Field(None, max_length=50, description="Microchip ID")
    allergies: Optional[str] = Field(None, description="Known allergies")
    medical_notes: Optional[str] = Field(None, description="Medical notes")
    temperament: Optional[str] = Field(None, max_length=100, description="Temperament")
    special_instructions: Optional[str] = Field(None, description="Special care instructions")
    owner_name: Optional[str] = Field(None, max_length=200, description="Owner name")
    owner_phone: Optional[str] = Field(None, max_length=30, description="Owner phone")
    photo_url: Optional[str] = Field(None, max_length=500, description="Photo URL")


class PetCreate(PetBase):
    """Schema for creating a new pet"""
    customer_id: Optional[UUID] = Field(None, description="Link to customer")


class PetUpdate(BaseModel):
    """Schema for updating a pet (all fields optional)"""
    name: Optional[str] = Field(None, max_length=100)
    species: Optional[PetSpeciesEnum] = None
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[PetSizeEnum] = None
    birth_date: Optional[datetime] = None
    weight_kg: Optional[float] = Field(None, ge=0, le=200)
    microchip_id: Optional[str] = Field(None, max_length=50)
    allergies: Optional[str] = None
    medical_notes: Optional[str] = None
    temperament: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    owner_name: Optional[str] = Field(None, max_length=200)
    owner_phone: Optional[str] = Field(None, max_length=30)
    photo_url: Optional[str] = Field(None, max_length=500)
    customer_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class PetRead(PetBase):
    """Schema for reading a pet"""
    id: UUID
    customer_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# APPOINTMENT SCHEMAS
# ================================================================

class AppointmentBase(BaseModel):
    """Base appointment fields"""
    service_type: WashServiceTypeEnum = Field(
        default=WashServiceTypeEnum.BASIC_WASH,
        description="Service type"
    )
    scheduled_at: datetime = Field(..., description="Scheduled date/time")
    duration_minutes: int = Field(default=30, ge=15, le=180, description="Duration")
    notes: Optional[str] = Field(None, description="Appointment notes")


class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment"""
    pet_id: UUID = Field(..., description="Pet ID")
    price: Optional[float] = Field(None, ge=0, description="Price in CHF")


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment"""
    service_type: Optional[WashServiceTypeEnum] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=180)
    status: Optional[AppointmentStatusEnum] = None
    price: Optional[float] = Field(None, ge=0)
    paid: Optional[bool] = None
    notes: Optional[str] = None
    groomer_notes: Optional[str] = None


class AppointmentRead(AppointmentBase):
    """Schema for reading an appointment"""
    id: UUID
    pet_id: UUID
    status: AppointmentStatusEnum
    price: Optional[float] = None
    paid: bool
    groomer_notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AppointmentWithPet(AppointmentRead):
    """Appointment with pet details included"""
    pet: PetRead


# ================================================================
# STATS & DASHBOARD
# ================================================================

class PetWashStats(BaseModel):
    """Pet wash station statistics - for Michel"""
    total_pets: int
    total_appointments: int
    appointments_today: int
    appointments_this_week: int
    revenue_today: float
    revenue_this_week: float
    pets_by_species: dict[str, int]
    popular_services: list[dict]
    upcoming_appointments: list[AppointmentWithPet]


class DailySchedule(BaseModel):
    """Daily appointment schedule"""
    date: datetime
    appointments: list[AppointmentWithPet]
    total_slots: int
    booked_slots: int


# ================================================================
# PRICING
# ================================================================

class ServicePriceRequest(BaseModel):
    """Request to get service price"""
    service_type: WashServiceTypeEnum
    size: PetSizeEnum


class ServicePriceResponse(BaseModel):
    """Service price response"""
    service_type: WashServiceTypeEnum
    size: PetSizeEnum
    price_chf: float
    duration_minutes: int


# ================================================================
# ZONES & CAMERA ENUMS
# ================================================================

class WashZoneEnum(str, Enum):
    """Wash station zones"""
    FRONT_CATS = "front_cats"
    FRONT_SMALL_DOGS = "front_small"
    FRONT_BIRDS = "front_birds"
    BACK_LAB = "back_lab"
    BACK_HUSKY = "back_husky"


class CameraStatusEnum(str, Enum):
    """Camera status"""
    OFFLINE = "offline"
    RECORDING = "recording"
    LIVE = "live"
    PROCESSING = "processing"


class MediaStatusEnum(str, Enum):
    """Media processing status"""
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    PURCHASED = "purchased"
    EXPIRED = "expired"


# ================================================================
# GROOMER SCHEMAS - Michel, Andy, Gerry
# ================================================================

class GroomerBase(BaseModel):
    """Base groomer fields"""
    name: str = Field(..., max_length=100, description="Groomer name")
    nickname: Optional[str] = Field(None, max_length=50, description="The Dr. Suess name")
    phone: Optional[str] = Field(None, max_length=30, description="Phone (if they answer)")

    # Skills
    can_do_cats: bool = Field(default=False)
    can_do_small_dogs: bool = Field(default=False)
    can_do_medium_dogs: bool = Field(default=False)
    can_do_large_dogs: bool = Field(default=False)
    can_do_giant_dogs: bool = Field(default=False, description="Husky territory")
    can_do_birds: bool = Field(default=False)
    can_do_exotic: bool = Field(default=False, description="Michel only")
    youtube_certified: bool = Field(default=False, description="Emergency mode")

    # Zones
    allowed_zones: Optional[str] = Field(None, description="Comma-separated zones")

    # Behavior
    answers_phone: bool = Field(default=True, description="False for Michel")
    needs_supervision: bool = Field(default=False, description="Cameras always on")
    is_on_call: bool = Field(default=False, description="Can be summoned")


class GroomerCreate(GroomerBase):
    """Schema for creating a groomer"""
    pass


class GroomerUpdate(BaseModel):
    """Schema for updating a groomer"""
    name: Optional[str] = Field(None, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=30)
    can_do_cats: Optional[bool] = None
    can_do_small_dogs: Optional[bool] = None
    can_do_medium_dogs: Optional[bool] = None
    can_do_large_dogs: Optional[bool] = None
    can_do_giant_dogs: Optional[bool] = None
    can_do_birds: Optional[bool] = None
    can_do_exotic: Optional[bool] = None
    youtube_certified: Optional[bool] = None
    allowed_zones: Optional[str] = None
    answers_phone: Optional[bool] = None
    needs_supervision: Optional[bool] = None
    is_on_call: Optional[bool] = None
    is_active: Optional[bool] = None


class GroomerRead(GroomerBase):
    """Schema for reading a groomer"""
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# WASH STATION SCHEMAS - With Cameras
# ================================================================

class WashStationBase(BaseModel):
    """Base wash station fields"""
    name: str = Field(..., max_length=50, description="Station name: TUB_1, TUB_2")
    zone: WashZoneEnum = Field(..., description="Which zone")
    can_handle_species: str = Field(default="dog,cat", description="Comma-separated species")
    max_pet_size: PetSizeEnum = Field(default=PetSizeEnum.MEDIUM)
    has_dryer: bool = Field(default=True)
    has_grooming_table: bool = Field(default=False)
    has_camera: bool = Field(default=True, description="For recording sessions")
    camera_url: Optional[str] = Field(None, max_length=500, description="RTSP stream URL")


class WashStationCreate(WashStationBase):
    """Schema for creating a wash station"""
    pass


class WashStationUpdate(BaseModel):
    """Schema for updating a wash station"""
    name: Optional[str] = Field(None, max_length=50)
    zone: Optional[WashZoneEnum] = None
    can_handle_species: Optional[str] = None
    max_pet_size: Optional[PetSizeEnum] = None
    has_dryer: Optional[bool] = None
    has_grooming_table: Optional[bool] = None
    has_camera: Optional[bool] = None
    camera_url: Optional[str] = Field(None, max_length=500)
    camera_status: Optional[CameraStatusEnum] = None
    is_available: Optional[bool] = None


class WashStationRead(WashStationBase):
    """Schema for reading a wash station"""
    id: UUID
    camera_status: CameraStatusEnum
    is_available: bool
    current_appointment_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# MEDIA SESSION SCHEMAS - The Roller Coaster Photo Model
# ================================================================

class MediaSessionBase(BaseModel):
    """Base media session fields"""
    appointment_id: UUID
    pet_id: UUID
    station_id: Optional[UUID] = None
    groomer_id: Optional[UUID] = None


class MediaSessionCreate(MediaSessionBase):
    """Schema for creating a media session (auto-created with appointment)"""
    pass


class MediaSessionRead(MediaSessionBase):
    """Schema for reading a media session"""
    id: UUID
    recording_started: Optional[datetime] = None
    recording_ended: Optional[datetime] = None

    # The Polaroids
    video_url: Optional[str] = None
    video_thumbnail_url: Optional[str] = None
    photo_before_url: Optional[str] = None
    photo_after_url: Optional[str] = None
    photo_action_url: Optional[str] = None

    # Status
    status: MediaStatusEnum
    processing_progress: int = 0

    # Preview - free teaser
    preview_url: Optional[str] = None

    # Expiry
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaSessionWithPet(MediaSessionRead):
    """Media session with pet info"""
    pet: PetRead
    groomer: Optional[GroomerRead] = None


# ================================================================
# MEDIA PURCHASE SCHEMAS - When They Buy the Polaroid
# ================================================================

class MediaPackageEnum(str, Enum):
    """Available media packages"""
    PHOTO_PACK = "photo_pack"           # CHF 15 - Before + After + Action
    VIDEO_CLIP = "video_clip"           # CHF 25 - 2-min highlight
    FULL_VIDEO = "full_video"           # CHF 45 - Full session
    DELUXE_PACK = "deluxe_pack"         # CHF 55 - Everything
    DIGITAL_FRAME = "digital_frame"     # CHF 10 - Just glamour shot


class MediaPurchaseCreate(BaseModel):
    """Schema for purchasing media"""
    media_session_id: UUID
    package: MediaPackageEnum = Field(..., description="Which package to buy")
    customer_id: Optional[UUID] = None
    email_to: Optional[str] = Field(None, max_length=255, description="Send download link here")


class MediaPurchaseRead(BaseModel):
    """Schema for reading a media purchase"""
    id: UUID
    media_session_id: UUID
    customer_id: Optional[UUID] = None

    # What they got
    includes_video: bool
    includes_photos: bool
    includes_before_after: bool

    # Pricing
    price_chf: float
    paid: bool

    # Delivery
    download_url: Optional[str] = None
    download_count: int
    emailed_to: Optional[str] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# MEDIA PRICING RESPONSE
# ================================================================

class MediaPricingResponse(BaseModel):
    """All media package prices"""
    photo_pack: float = 15.00
    video_clip: float = 25.00
    full_video: float = 45.00
    deluxe_pack: float = 55.00
    digital_frame: float = 10.00


# ================================================================
# GROOMER AVAILABILITY & SCHEDULING
# ================================================================

class GroomerSchedule(BaseModel):
    """Groomer's daily schedule"""
    groomer: GroomerRead
    date: datetime
    appointments: list[AppointmentRead]
    available_slots: list[datetime]


class StationStatus(BaseModel):
    """Current status of all wash stations"""
    stations: list[WashStationRead]
    available_count: int
    in_use_count: int
    cameras_recording: int
