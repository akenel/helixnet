# File: src/schemas/cat_schema.py
"""
Pydantic schemas for HelixCAT.
Cats only. No dogs. Peter's way.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class CatSizeEnum(str, Enum):
    KITTEN = "kitten"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    CHONK = "chonk"


class CoatTypeEnum(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    HAIRLESS = "hairless"
    CURLY = "curly"


class CatTemperamentEnum(str, Enum):
    CHILL = "chill"
    NERVOUS = "nervous"
    SPICY = "spicy"
    ANGEL = "angel"
    WILDCARD = "wildcard"


class ServiceTypeEnum(str, Enum):
    BASIC_GROOM = "basic_groom"
    FULL_GROOM = "full_groom"
    BATH_ONLY = "bath_only"
    NAIL_TRIM = "nail_trim"
    LION_CUT = "lion_cut"
    MAT_REMOVAL = "mat_removal"
    SPA_DAY = "spa_day"
    FLEA_TREATMENT = "flea_treatment"


class AppointmentStatusEnum(str, Enum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    DRYING = "drying"
    READY = "ready"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class MembershipTypeEnum(str, Enum):
    SINGLE_VISIT = "single_visit"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    VIP_CAT = "vip_cat"


# ================================================================
# CAT SCHEMAS
# ================================================================

class CatBase(BaseModel):
    name: str = Field(..., max_length=100)
    nickname: Optional[str] = Field(None, max_length=100)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=100)
    size: CatSizeEnum = CatSizeEnum.MEDIUM
    coat_type: CoatTypeEnum = CoatTypeEnum.SHORT
    weight_kg: Optional[float] = Field(None, ge=0)
    temperament: CatTemperamentEnum = CatTemperamentEnum.CHILL
    microchip_id: Optional[str] = Field(None, max_length=50)
    is_neutered: bool = True
    birth_date: Optional[date] = None
    medical_notes: Optional[str] = None
    allergies: Optional[str] = None
    favorite_treats: Optional[str] = Field(None, max_length=200)
    hates: Optional[str] = Field(None, max_length=200)
    special_handling: Optional[str] = None


class CatCreate(CatBase):
    owner_id: UUID


class CatUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    nickname: Optional[str] = Field(None, max_length=100)
    size: Optional[CatSizeEnum] = None
    coat_type: Optional[CoatTypeEnum] = None
    weight_kg: Optional[float] = Field(None, ge=0)
    temperament: Optional[CatTemperamentEnum] = None
    medical_notes: Optional[str] = None
    allergies: Optional[str] = None
    special_handling: Optional[str] = None
    is_active: Optional[bool] = None
    is_vip: Optional[bool] = None
    needs_two_groomers: Optional[bool] = None


class CatRead(CatBase):
    id: UUID
    owner_id: UUID
    total_visits: int
    last_visit: Optional[datetime] = None
    is_active: bool
    is_vip: bool
    needs_two_groomers: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CAT OWNER SCHEMAS
# ================================================================

class CatOwnerBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: str = Field(..., max_length=30)
    phone_alt: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class CatOwnerCreate(CatOwnerBase):
    membership_type: MembershipTypeEnum = MembershipTypeEnum.SINGLE_VISIT


class CatOwnerRead(CatOwnerBase):
    id: UUID
    membership_type: MembershipTypeEnum
    membership_expires: Optional[date] = None
    total_spent: float
    total_visits: int
    is_active: bool
    is_vip: bool
    allows_photos: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CatOwnerWithCats(CatOwnerRead):
    cats: list[CatRead] = []


# ================================================================
# SERVICE SCHEMAS
# ================================================================

class CatServiceBase(BaseModel):
    name: str = Field(..., max_length=100)
    service_type: ServiceTypeEnum
    description: Optional[str] = None
    price_kitten: float = Field(default=0, ge=0)
    price_small: float = Field(default=0, ge=0)
    price_medium: float = Field(default=0, ge=0)
    price_large: float = Field(default=0, ge=0)
    price_chonk: float = Field(default=0, ge=0)
    duration_minutes: int = Field(default=60, ge=15)
    includes_nail_trim: bool = False
    includes_ear_clean: bool = False
    includes_photo: bool = False


class CatServiceCreate(CatServiceBase):
    pass


class CatServiceRead(CatServiceBase):
    id: UUID
    is_active: bool
    requires_booking: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# APPOINTMENT SCHEMAS
# ================================================================

class AppointmentCreate(BaseModel):
    cat_id: UUID
    service_id: UUID
    groomer_id: Optional[UUID] = None
    appointment_date: date
    appointment_time: datetime
    special_requests: Optional[str] = None


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatusEnum] = None
    groomer_id: Optional[UUID] = None
    groomer_notes: Optional[str] = None
    cat_was_spicy: Optional[bool] = None
    extras_price: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)


class AppointmentRead(BaseModel):
    id: UUID
    cat_id: UUID
    service_id: UUID
    groomer_id: Optional[UUID] = None
    appointment_date: date
    appointment_time: datetime
    estimated_duration: int
    status: AppointmentStatusEnum
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    base_price: float
    extras_price: float
    discount: float
    total_price: float
    is_paid: bool
    payment_method: Optional[str] = None
    special_requests: Optional[str] = None
    groomer_notes: Optional[str] = None
    is_first_visit: bool
    cat_was_spicy: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentDetail(AppointmentRead):
    cat: CatRead
    service: CatServiceRead


# ================================================================
# GROOMER SCHEMAS
# ================================================================

class GroomerBase(BaseModel):
    name: str = Field(..., max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=255)
    can_handle_spicy: bool = False
    can_do_lion_cut: bool = False
    can_do_mat_removal: bool = True
    certified_feline: bool = False
    years_experience: int = Field(default=0, ge=0)


class GroomerCreate(GroomerBase):
    pass


class GroomerRead(GroomerBase):
    id: UUID
    works_monday: bool
    works_tuesday: bool
    works_wednesday: bool
    works_thursday: bool
    works_friday: bool
    works_saturday: bool
    works_sunday: bool
    cats_groomed: int
    avg_rating: float
    scratches_received: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK ACTIONS
# ================================================================

class QuickCheckIn(BaseModel):
    """Quick check-in for walk-in or booked cat"""
    appointment_id: Optional[UUID] = None
    cat_id: Optional[UUID] = None
    service_type: Optional[ServiceTypeEnum] = ServiceTypeEnum.BASIC_GROOM
    notes: Optional[str] = None


class QuickCheckOut(BaseModel):
    """Quick checkout and payment"""
    appointment_id: UUID
    payment_method: str = Field(..., max_length=50)
    tip: float = Field(default=0, ge=0)
    cat_was_spicy: bool = False
    groomer_notes: Optional[str] = None


class QuickPhoto(BaseModel):
    """Quick photo upload"""
    cat_id: UUID
    appointment_id: Optional[UUID] = None
    photo_type: str = Field(default="after", max_length=20)
    can_use_marketing: bool = False


# ================================================================
# DASHBOARD SCHEMAS
# ================================================================

class TodayDashboard(BaseModel):
    """Daily dashboard for Peter"""
    today_date: date
    appointments_today: int
    completed: int
    in_progress: int
    waiting: int
    revenue_today: float
    cats_groomed: int
    spicy_cats: int
    next_appointment: Optional[AppointmentDetail] = None


class CatStats(BaseModel):
    """Cat statistics"""
    total_cats: int
    active_cats: int
    vip_cats: int
    spicy_cats: int
    most_common_breed: Optional[str] = None
    most_common_service: Optional[str] = None


class GroomerStats(BaseModel):
    """Groomer leaderboard"""
    groomer_id: UUID
    name: str
    cats_this_month: int
    avg_rating: float
    scratches_this_month: int
    revenue_generated: float


# ================================================================
# SEARCH
# ================================================================

class CatSearch(BaseModel):
    query: Optional[str] = None
    size: Optional[CatSizeEnum] = None
    temperament: Optional[CatTemperamentEnum] = None
    is_vip: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AppointmentSearch(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[AppointmentStatusEnum] = None
    groomer_id: Optional[UUID] = None
    cat_id: Optional[UUID] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
