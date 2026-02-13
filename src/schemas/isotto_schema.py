# File: src/schemas/isotto_schema.py
"""
Pydantic schemas for ISOTTO Sport Print Shop.
Used for request validation and response serialization.
Following the camper_schema.py pattern exactly.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional

from src.db.models.isotto_order_model import ProductType, OrderStatus, ColorMode, DuplexMode, Lamination


# ================================================================
# CUSTOMER SCHEMAS
# ================================================================

class IsottoCustomerBase(BaseModel):
    """Base customer fields"""
    name: str = Field(..., max_length=200, description="Full name")
    company_name: Optional[str] = Field(None, max_length=300, description="Business name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50, description="Codice Fiscale or P.IVA")
    notes: Optional[str] = None


class IsottoCustomerCreate(IsottoCustomerBase):
    """Schema for creating a new customer"""
    pass


class IsottoCustomerUpdate(BaseModel):
    """Schema for updating customer (all fields optional)"""
    name: Optional[str] = Field(None, max_length=200)
    company_name: Optional[str] = Field(None, max_length=300)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class IsottoCustomerRead(IsottoCustomerBase):
    """Schema for reading customer (includes DB fields)"""
    id: UUID
    first_order_date: Optional[date] = None
    last_order_date: Optional[date] = None
    order_count: int
    total_spend: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# PRINT ORDER SCHEMAS
# ================================================================

class PrintOrderBase(BaseModel):
    """Base print order fields"""
    title: str = Field(..., max_length=200, description="Short description")
    description: Optional[str] = None
    customer_id: UUID
    product_type: ProductType = Field(default=ProductType.POSTCARD)
    quantity: int = Field(default=0, ge=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    # Print specs
    paper_weight_gsm: Optional[int] = Field(None, ge=0)
    color_mode: Optional[ColorMode] = ColorMode.CMYK
    duplex: bool = False
    duplex_mode: Optional[DuplexMode] = None
    lamination: Optional[Lamination] = Lamination.NONE
    size_description: Optional[str] = Field(None, max_length=100)
    copies_per_sheet: Optional[int] = Field(None, ge=1)
    cutting_instructions: Optional[str] = None
    finishing_notes: Optional[str] = None
    # Files
    artwork_files: Optional[str] = None
    # Production
    assigned_to: Optional[str] = Field(None, max_length=100, description="Operator name")
    estimated_completion: Optional[date] = None
    # Notes
    customer_notes: Optional[str] = None


class PrintOrderCreate(PrintOrderBase):
    """Schema for creating a new print order (starts as QUOTED)"""
    pass


class PrintOrderUpdate(BaseModel):
    """Schema for updating print order (all fields optional)"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    product_type: Optional[ProductType] = None
    quantity: Optional[int] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    paper_weight_gsm: Optional[int] = Field(None, ge=0)
    color_mode: Optional[ColorMode] = None
    duplex: Optional[bool] = None
    duplex_mode: Optional[DuplexMode] = None
    lamination: Optional[Lamination] = None
    size_description: Optional[str] = Field(None, max_length=100)
    copies_per_sheet: Optional[int] = Field(None, ge=1)
    cutting_instructions: Optional[str] = None
    finishing_notes: Optional[str] = None
    artwork_files: Optional[str] = None
    proof_approved: Optional[bool] = None
    assigned_to: Optional[str] = Field(None, max_length=100)
    estimated_completion: Optional[date] = None
    customer_notes: Optional[str] = None
    production_notes: Optional[str] = None


class PrintOrderStatusUpdate(BaseModel):
    """Schema for advancing order status"""
    status: OrderStatus


class PrintOrderRead(BaseModel):
    """Schema for reading print order (includes DB fields)"""
    id: UUID
    order_number: str
    title: str
    description: Optional[str] = None
    customer_id: UUID
    product_type: ProductType
    status: OrderStatus
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    currency: str
    paper_weight_gsm: Optional[int] = None
    color_mode: Optional[ColorMode] = None
    duplex: bool
    duplex_mode: Optional[DuplexMode] = None
    lamination: Optional[Lamination] = None
    size_description: Optional[str] = None
    copies_per_sheet: Optional[int] = None
    cutting_instructions: Optional[str] = None
    finishing_notes: Optional[str] = None
    artwork_files: Optional[str] = None
    proof_approved: bool
    proof_approved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    estimated_completion: Optional[date] = None
    quoted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    production_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    customer_notes: Optional[str] = None
    production_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DASHBOARD SCHEMA
# ================================================================

class IsottoDashboardSummary(BaseModel):
    """Dashboard stats for Famous Guy's one-screen overview"""
    orders_in_production: int = Field(description="Orders currently being printed")
    orders_pending_approval: int = Field(description="Quotes awaiting customer approval")
    orders_ready: int = Field(description="Orders ready for pickup")
    orders_completed_today: int = Field(description="Orders finished today")
    orders_in_quality_check: int = Field(description="Orders in quality check")
    total_orders: int = Field(description="All-time order count")
