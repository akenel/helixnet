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
