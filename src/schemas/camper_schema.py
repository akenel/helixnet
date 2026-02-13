# File: src/schemas/camper_schema.py
"""
Pydantic schemas for Camper & Tour Service Management.
Used for request validation and response serialization.
Following the pos_schema.py pattern exactly.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional

from src.db.models.camper_vehicle_model import VehicleType, VehicleStatus
from src.db.models.camper_customer_model import CustomerLanguage
from src.db.models.camper_service_job_model import JobType, JobStatus


# ================================================================
# VEHICLE SCHEMAS
# ================================================================

class VehicleBase(BaseModel):
    """Base vehicle fields"""
    registration_plate: str = Field(..., max_length=20, description="License plate")
    chassis_number: Optional[str] = Field(None, max_length=50, description="VIN / chassis number")
    vehicle_type: VehicleType = Field(default=VehicleType.CAMPERVAN)
    make: Optional[str] = Field(None, max_length=100, description="e.g., Fiat, Mercedes, VW")
    model: Optional[str] = Field(None, max_length=100, description="e.g., Ducato, Sprinter")
    year: Optional[int] = Field(None, ge=1950, le=2030)
    color: Optional[str] = Field(None, max_length=50)
    length_m: Optional[float] = Field(None, ge=0)
    height_m: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    owner_name: Optional[str] = Field(None, max_length=200)
    owner_phone: Optional[str] = Field(None, max_length=50)
    owner_email: Optional[str] = Field(None, max_length=255)
    owner_id: Optional[UUID] = Field(None, description="FK to customer profile")
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_policy: Optional[str] = Field(None, max_length=100)
    photos: Optional[str] = Field(None, description="Comma-separated photo URLs")
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    """Schema for registering a new vehicle"""
    pass


class VehicleUpdate(BaseModel):
    """Schema for updating vehicle (all fields optional)"""
    registration_plate: Optional[str] = Field(None, max_length=20)
    chassis_number: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[VehicleType] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1950, le=2030)
    color: Optional[str] = Field(None, max_length=50)
    length_m: Optional[float] = Field(None, ge=0)
    height_m: Optional[float] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    owner_name: Optional[str] = Field(None, max_length=200)
    owner_phone: Optional[str] = Field(None, max_length=50)
    owner_email: Optional[str] = Field(None, max_length=255)
    owner_id: Optional[UUID] = None
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_policy: Optional[str] = Field(None, max_length=100)
    photos: Optional[str] = None
    notes: Optional[str] = None


class VehicleRead(VehicleBase):
    """Schema for reading vehicle (includes DB fields)"""
    id: UUID
    status: VehicleStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleStatusUpdate(BaseModel):
    """Schema for changing vehicle status"""
    status: VehicleStatus


# ================================================================
# CUSTOMER SCHEMAS
# ================================================================

class CamperCustomerBase(BaseModel):
    """Base customer fields"""
    name: str = Field(..., max_length=200, description="Full name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    language: CustomerLanguage = Field(default=CustomerLanguage.IT)
    tax_id: Optional[str] = Field(None, max_length=50, description="Codice Fiscale or P.IVA")
    notes: Optional[str] = None


class CamperCustomerCreate(CamperCustomerBase):
    """Schema for creating a new customer"""
    pass


class CamperCustomerUpdate(BaseModel):
    """Schema for updating customer (all fields optional)"""
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    language: Optional[CustomerLanguage] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class CamperCustomerRead(CamperCustomerBase):
    """Schema for reading customer (includes DB fields)"""
    id: UUID
    first_visit: Optional[date] = None
    last_visit: Optional[date] = None
    visit_count: int
    total_spend: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SERVICE JOB SCHEMAS
# ================================================================

class ServiceJobBase(BaseModel):
    """Base service job fields"""
    title: str = Field(..., max_length=200, description="Short description")
    description: Optional[str] = None
    vehicle_id: UUID
    customer_id: UUID
    job_type: JobType = Field(default=JobType.REPAIR)
    assigned_to: Optional[str] = Field(None, max_length=100, description="Mechanic name")
    estimated_hours: float = Field(default=0, ge=0)
    estimated_parts_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    estimated_total: Decimal = Field(default=Decimal("0.00"), ge=0)
    quote_valid_until: Optional[date] = None
    scheduled_date: Optional[date] = None
    customer_notes: Optional[str] = None


class ServiceJobCreate(ServiceJobBase):
    """Schema for creating a new service job (starts as QUOTED)"""
    pass


class ServiceJobUpdate(BaseModel):
    """Schema for updating service job (all fields optional)"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    job_type: Optional[JobType] = None
    assigned_to: Optional[str] = Field(None, max_length=100)
    estimated_hours: Optional[float] = Field(None, ge=0)
    estimated_parts_cost: Optional[Decimal] = Field(None, ge=0)
    estimated_total: Optional[Decimal] = Field(None, ge=0)
    quote_valid_until: Optional[date] = None
    actual_hours: Optional[float] = Field(None, ge=0)
    actual_parts_cost: Optional[Decimal] = Field(None, ge=0)
    actual_labor_cost: Optional[Decimal] = Field(None, ge=0)
    actual_total: Optional[Decimal] = Field(None, ge=0)
    parts_used: Optional[str] = None
    parts_on_order: Optional[bool] = None
    parts_po_number: Optional[str] = Field(None, max_length=50)
    scheduled_date: Optional[date] = None
    issue_found: Optional[str] = None
    work_performed: Optional[str] = None
    before_photos: Optional[str] = None
    after_photos: Optional[str] = None
    customer_notes: Optional[str] = None
    mechanic_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_notes: Optional[str] = None
    next_service_date: Optional[date] = None


class ServiceJobStatusUpdate(BaseModel):
    """Schema for advancing job status"""
    status: JobStatus


class ServiceJobRead(BaseModel):
    """Schema for reading service job (includes DB fields)"""
    id: UUID
    job_number: str
    title: str
    description: Optional[str] = None
    vehicle_id: UUID
    customer_id: UUID
    job_type: JobType
    status: JobStatus
    assigned_to: Optional[str] = None
    estimated_hours: float
    estimated_parts_cost: Decimal
    estimated_total: Decimal
    quote_valid_until: Optional[date] = None
    actual_hours: float
    actual_parts_cost: Decimal
    actual_labor_cost: Decimal
    actual_total: Decimal
    currency: str
    parts_used: Optional[str] = None
    parts_on_order: bool
    parts_po_number: Optional[str] = None
    scheduled_date: Optional[date] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    issue_found: Optional[str] = None
    work_performed: Optional[str] = None
    before_photos: Optional[str] = None
    after_photos: Optional[str] = None
    customer_notes: Optional[str] = None
    mechanic_notes: Optional[str] = None
    follow_up_required: bool
    follow_up_notes: Optional[str] = None
    next_service_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DASHBOARD SCHEMA
# ================================================================

class DashboardSummary(BaseModel):
    """Dashboard stats for Nino's one-screen overview"""
    vehicles_in_shop: int = Field(description="Vehicles currently checked in or in service")
    jobs_in_progress: int = Field(description="Active jobs being worked on")
    jobs_waiting_parts: int = Field(description="Jobs blocked on parts")
    jobs_completed_today: int = Field(description="Jobs finished today")
    pending_quotes: int = Field(description="Quotes awaiting customer approval")
    total_jobs: int = Field(description="All-time job count")
