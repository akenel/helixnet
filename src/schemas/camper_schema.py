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
from typing import Optional, Any

from src.db.models.camper_vehicle_model import VehicleType, VehicleStatus
from src.db.models.camper_customer_model import CustomerLanguage
from src.db.models.camper_service_job_model import JobType, JobStatus
from src.db.models.camper_quotation_model import QuotationStatus
from src.db.models.camper_purchase_order_model import CamperPOStatus
from src.db.models.camper_invoice_model import PaymentStatus


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
    telegram_chat_id: Optional[str] = Field(None, max_length=50, description="Telegram bot chat ID")
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
    telegram_chat_id: Optional[str] = Field(None, max_length=50)
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
    # Optimistic locking: client sends the updated_at it read, server rejects if stale
    expected_updated_at: Optional[datetime] = Field(None, description="Send the updated_at you read. Rejects if another write happened since.")


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
    # Inspection fields
    inspection_passed: bool = False
    inspection_notes: Optional[str] = None
    inspected_by: Optional[str] = None
    inspected_at: Optional[datetime] = None
    # Deposit fields
    deposit_required: Decimal = Decimal("0.00")
    deposit_paid: Decimal = Decimal("0.00")
    deposit_paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUOTATION SCHEMAS
# ================================================================

class QuotationLineItem(BaseModel):
    """A single line item on a quotation"""
    description: str = Field(..., max_length=500)
    quantity: float = Field(default=1, ge=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(default=Decimal("0.00"), ge=0)
    item_type: str = Field(default="labor", description="labor, parts, or materials")


class QuotationCreate(BaseModel):
    """Schema for creating a quotation"""
    job_id: UUID
    customer_id: UUID
    vehicle_id: UUID
    line_items: list[QuotationLineItem] = Field(default_factory=list)
    vat_rate: Decimal = Field(default=Decimal("22.00"))
    deposit_percent: Decimal = Field(default=Decimal("25.00"))
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuotationUpdate(BaseModel):
    """Schema for updating quotation (all fields optional)"""
    line_items: Optional[list[QuotationLineItem]] = None
    vat_rate: Optional[Decimal] = None
    deposit_percent: Optional[Decimal] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class QuotationRead(BaseModel):
    """Schema for reading quotation"""
    id: UUID
    quote_number: str
    job_id: UUID
    customer_id: UUID
    vehicle_id: UUID
    line_items: list[Any] = Field(default_factory=list)
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str
    deposit_percent: Decimal
    deposit_amount: Decimal
    valid_until: Optional[date] = None
    notes: Optional[str] = None
    status: QuotationStatus
    sent_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PURCHASE ORDER SCHEMAS
# ================================================================

class POLineItem(BaseModel):
    """A single line item on a purchase order"""
    description: str = Field(..., max_length=500)
    part_number: Optional[str] = Field(None, max_length=100)
    quantity: float = Field(default=1, ge=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(default=Decimal("0.00"), ge=0)


class PurchaseOrderCreate(BaseModel):
    """Schema for creating a purchase order"""
    job_id: UUID
    supplier_name: str = Field(..., max_length=200)
    supplier_contact: Optional[str] = Field(None, max_length=200)
    supplier_email: Optional[str] = Field(None, max_length=255)
    supplier_phone: Optional[str] = Field(None, max_length=50)
    line_items: list[POLineItem] = Field(default_factory=list)
    vat_rate: Decimal = Field(default=Decimal("22.00"))
    expected_delivery: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating purchase order"""
    supplier_name: Optional[str] = Field(None, max_length=200)
    supplier_contact: Optional[str] = Field(None, max_length=200)
    supplier_email: Optional[str] = Field(None, max_length=255)
    supplier_phone: Optional[str] = Field(None, max_length=50)
    line_items: Optional[list[POLineItem]] = None
    vat_rate: Optional[Decimal] = None
    expected_delivery: Optional[date] = None
    tracking_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class POStatusUpdate(BaseModel):
    """Schema for advancing PO status"""
    status: CamperPOStatus


class PurchaseOrderRead(BaseModel):
    """Schema for reading purchase order"""
    id: UUID
    po_number: str
    job_id: UUID
    supplier_name: str
    supplier_contact: Optional[str] = None
    supplier_email: Optional[str] = None
    supplier_phone: Optional[str] = None
    line_items: list[Any] = Field(default_factory=list)
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str
    status: CamperPOStatus
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# INVOICE SCHEMAS
# ================================================================

class InvoiceCreate(BaseModel):
    """Schema for creating an invoice from a completed job"""
    job_id: UUID
    customer_id: UUID
    quotation_id: Optional[UUID] = None
    line_items: list[QuotationLineItem] = Field(default_factory=list)
    vat_rate: Decimal = Field(default=Decimal("22.00"))
    deposit_applied: Decimal = Field(default=Decimal("0.00"))
    due_date: date
    notes: Optional[str] = None


class InvoiceRead(BaseModel):
    """Schema for reading invoice"""
    id: UUID
    invoice_number: str
    job_id: UUID
    customer_id: UUID
    quotation_id: Optional[UUID] = None
    line_items: list[Any] = Field(default_factory=list)
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str
    deposit_applied: Decimal
    amount_due: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    due_date: date
    pdf_url: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoicePayment(BaseModel):
    """Schema for marking invoice as paid"""
    payment_method: str = Field(..., description="cash, card, transfer")


# ================================================================
# DOCUMENT SCHEMAS
# ================================================================

class DocumentRead(BaseModel):
    """Schema for reading document metadata"""
    id: UUID
    entity_type: str
    entity_id: UUID
    file_name: str
    file_type: str
    file_size: int
    description: Optional[str] = None
    uploaded_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CALENDAR SCHEMA
# ================================================================

class CalendarEvent(BaseModel):
    """Job projected into calendar format for FullCalendar.js"""
    id: str
    title: str
    start: str
    end: Optional[str] = None
    color: str
    url: str
    extendedProps: dict = Field(default_factory=dict)


# ================================================================
# INSPECTION SCHEMAS
# ================================================================

class InspectionResult(BaseModel):
    """Schema for inspection pass/fail"""
    notes: Optional[str] = None


# ================================================================
# DEPOSIT SCHEMA
# ================================================================

class DepositPayment(BaseModel):
    """Schema for recording deposit payment"""
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(default="cash", description="cash, card, transfer")


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
    pending_deposits: Decimal = Field(default=Decimal("0.00"), description="Total deposits awaiting payment")
    total_revenue_month: Decimal = Field(default=Decimal("0.00"), description="Invoice revenue this month")
    overdue_invoices: int = Field(default=0, description="Invoices past due date")
    jobs_in_inspection: int = Field(default=0, description="Jobs awaiting inspection")
