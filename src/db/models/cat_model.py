# File: src/db/models/cat_model.py
"""
HelixCAT - Cats Only. No Dogs. Peter's Way.
Be Water.
"""
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, date
from uuid import uuid4
import enum

from src.db.models.base import Base


# ================================================================
# ENUMS - CATS ONLY
# ================================================================

class CatSize(enum.Enum):
    KITTEN = "kitten"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    CHONK = "chonk"


class CoatType(enum.Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    HAIRLESS = "hairless"
    CURLY = "curly"


class CatTemperament(enum.Enum):
    CHILL = "chill"
    NERVOUS = "nervous"
    SPICY = "spicy"
    ANGEL = "angel"
    WILDCARD = "wildcard"


class ServiceType(enum.Enum):
    BASIC_GROOM = "basic_groom"
    FULL_GROOM = "full_groom"
    BATH_ONLY = "bath_only"
    NAIL_TRIM = "nail_trim"
    LION_CUT = "lion_cut"
    MAT_REMOVAL = "mat_removal"
    SPA_DAY = "spa_day"
    FLEA_TREATMENT = "flea_treatment"


class AppointmentStatus(enum.Enum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    DRYING = "drying"
    READY = "ready"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class MembershipType(enum.Enum):
    SINGLE_VISIT = "single_visit"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    VIP_CAT = "vip_cat"


# ================================================================
# CAT MODEL - THE STAR
# ================================================================

class CatModel(Base):
    """Every cat is a star. No dogs allowed."""
    __tablename__ = 'cats'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=True)
    breed: Mapped[str] = mapped_column(String(100), nullable=True)
    color: Mapped[str] = mapped_column(String(100), nullable=True)

    # Physical
    size: Mapped[CatSize] = mapped_column(
        SQLEnum(CatSize), default=CatSize.MEDIUM
    )
    coat_type: Mapped[CoatType] = mapped_column(
        SQLEnum(CoatType), default=CoatType.SHORT
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=True)

    # Personality - important for grooming
    temperament: Mapped[CatTemperament] = mapped_column(
        SQLEnum(CatTemperament), default=CatTemperament.CHILL
    )

    # Medical
    microchip_id: Mapped[str] = mapped_column(String(50), nullable=True)
    is_neutered: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    medical_notes: Mapped[str] = mapped_column(Text, nullable=True)
    allergies: Mapped[str] = mapped_column(Text, nullable=True)

    # Owner link
    owner_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cat_owners.id'), nullable=False
    )

    # Preferences
    favorite_treats: Mapped[str] = mapped_column(String(200), nullable=True)
    hates: Mapped[str] = mapped_column(String(200), nullable=True, comment="water, dryer, strangers")
    special_handling: Mapped[str] = mapped_column(Text, nullable=True)

    # Stats
    total_visits: Mapped[int] = mapped_column(Integer, default=0)
    last_visit: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_two_groomers: Mapped[bool] = mapped_column(Boolean, default=False, comment="Spicy cats")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped["CatOwnerModel"] = relationship(back_populates="cats")
    appointments: Mapped[list["CatAppointmentModel"]] = relationship(back_populates="cat")
    photos: Mapped[list["CatPhotoModel"]] = relationship(back_populates="cat")


# ================================================================
# CAT OWNER MODEL
# ================================================================

class CatOwnerModel(Base):
    """Cat parent. The human who pays."""
    __tablename__ = 'cat_owners'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    phone_alt: Mapped[str] = mapped_column(String(30), nullable=True)

    # Address
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=True)

    # Membership
    membership_type: Mapped[MembershipType] = mapped_column(
        SQLEnum(MembershipType), default=MembershipType.SINGLE_VISIT
    )
    membership_expires: Mapped[date] = mapped_column(Date, nullable=True)

    # Payment
    preferred_payment: Mapped[str] = mapped_column(String(50), nullable=True)

    # Stats
    total_spent: Mapped[float] = mapped_column(Float, default=0)
    total_visits: Mapped[int] = mapped_column(Integer, default=0)

    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    allows_photos: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    cats: Mapped[list["CatModel"]] = relationship(back_populates="owner")


# ================================================================
# SERVICE PACKAGE MODEL
# ================================================================

class CatServiceModel(Base):
    """Services we offer. Cats only."""
    __tablename__ = 'cat_services'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(SQLEnum(ServiceType))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Pricing by size
    price_kitten: Mapped[float] = mapped_column(Float, default=0)
    price_small: Mapped[float] = mapped_column(Float, default=0)
    price_medium: Mapped[float] = mapped_column(Float, default=0)
    price_large: Mapped[float] = mapped_column(Float, default=0)
    price_chonk: Mapped[float] = mapped_column(Float, default=0)

    # Time
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    # Extras
    includes_nail_trim: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_ear_clean: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_photo: Mapped[bool] = mapped_column(Boolean, default=False)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_booking: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ================================================================
# APPOINTMENT MODEL
# ================================================================

class CatAppointmentModel(Base):
    """Booking for cat grooming. No dogs in the queue."""
    __tablename__ = 'cat_appointments'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Links
    cat_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cats.id'), nullable=False
    )
    service_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cat_services.id'), nullable=False
    )
    groomer_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cat_groomers.id'), nullable=True
    )

    # Scheduling
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estimated_duration: Mapped[int] = mapped_column(Integer, default=60)

    # Status tracking
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus), default=AppointmentStatus.BOOKED
    )
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    picked_up_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Pricing
    base_price: Mapped[float] = mapped_column(Float, default=0)
    extras_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total_price: Mapped[float] = mapped_column(Float, default=0)

    # Payment
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Notes
    special_requests: Mapped[str] = mapped_column(Text, nullable=True)
    groomer_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Flags
    is_first_visit: Mapped[bool] = mapped_column(Boolean, default=False)
    cat_was_spicy: Mapped[bool] = mapped_column(Boolean, default=False, comment="For next time")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    cat: Mapped["CatModel"] = relationship(back_populates="appointments")
    service: Mapped["CatServiceModel"] = relationship()
    groomer: Mapped["CatGroomerModel"] = relationship()


# ================================================================
# CAT GROOMER MODEL
# ================================================================

class CatGroomerModel(Base):
    """Staff who groom cats. Cat specialists only."""
    __tablename__ = 'cat_groomers'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)

    # Skills
    can_handle_spicy: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_lion_cut: Mapped[bool] = mapped_column(Boolean, default=False)
    can_do_mat_removal: Mapped[bool] = mapped_column(Boolean, default=True)
    certified_feline: Mapped[bool] = mapped_column(Boolean, default=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)

    # Availability
    works_monday: Mapped[bool] = mapped_column(Boolean, default=True)
    works_tuesday: Mapped[bool] = mapped_column(Boolean, default=True)
    works_wednesday: Mapped[bool] = mapped_column(Boolean, default=True)
    works_thursday: Mapped[bool] = mapped_column(Boolean, default=True)
    works_friday: Mapped[bool] = mapped_column(Boolean, default=True)
    works_saturday: Mapped[bool] = mapped_column(Boolean, default=False)
    works_sunday: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    cats_groomed: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[float] = mapped_column(Float, default=5.0)
    scratches_received: Mapped[int] = mapped_column(Integer, default=0, comment="Battle scars")

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ================================================================
# CAT PHOTO MODEL - BEFORE/AFTER
# ================================================================

class CatPhotoModel(Base):
    """Before/after photos. The money shot."""
    __tablename__ = 'cat_photos'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    cat_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cats.id'), nullable=False
    )
    appointment_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('cat_appointments.id'), nullable=True
    )

    photo_type: Mapped[str] = mapped_column(String(20), default="after", comment="before, during, after")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # Social
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_marketing: Mapped[bool] = mapped_column(Boolean, default=False)
    likes: Mapped[int] = mapped_column(Integer, default=0)

    # Purchase
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False)
    purchase_price: Mapped[float] = mapped_column(Float, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    cat: Mapped["CatModel"] = relationship(back_populates="photos")


# ================================================================
# DAILY STATS MODEL
# ================================================================

class CatDailyStatsModel(Base):
    """Daily tracking. How many cats got fabulous."""
    __tablename__ = 'cat_daily_stats'

    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    stats_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)

    # Counts
    appointments_booked: Mapped[int] = mapped_column(Integer, default=0)
    appointments_completed: Mapped[int] = mapped_column(Integer, default=0)
    appointments_cancelled: Mapped[int] = mapped_column(Integer, default=0)
    no_shows: Mapped[int] = mapped_column(Integer, default=0)

    # Revenue
    total_revenue: Mapped[float] = mapped_column(Float, default=0)
    avg_ticket: Mapped[float] = mapped_column(Float, default=0)

    # Fun stats
    spicy_cats: Mapped[int] = mapped_column(Integer, default=0)
    lion_cuts: Mapped[int] = mapped_column(Integer, default=0)
    photos_sold: Mapped[int] = mapped_column(Integer, default=0)
    new_cats_registered: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
