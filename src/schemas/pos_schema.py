# File: src/schemas/pos_schema.py
"""
Pydantic schemas for POS (Point of Sale) system.
Used for request validation and response serialization.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
from src.db.models.transaction_model import TransactionStatus, PaymentMethod


# ================================================================
# PRODUCT SCHEMAS
# ================================================================

class ProductBase(BaseModel):
    """Base product fields"""
    barcode: Optional[str] = Field(None, max_length=100, description="EAN/UPC barcode")
    sku: str = Field(..., max_length=100, description="Internal SKU (required)")
    name: str = Field(..., max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Full description")
    price: Decimal = Field(..., ge=0, description="Sale price in CHF")
    cost: Optional[Decimal] = Field(None, ge=0, description="Cost price")
    stock_quantity: int = Field(default=0, ge=0, description="Current stock")
    stock_alert_threshold: Optional[int] = Field(None, ge=0, description="Low stock alert level")
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    is_active: bool = Field(default=True, description="Product available for sale")
    is_age_restricted: bool = Field(default=False, description="Requires 18+ ID")
    vending_compatible: bool = Field(default=False, description="Can be sold via vending machine")
    vending_slot: Optional[int] = Field(None, description="Vending machine slot number")


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating product (all fields optional)"""
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    stock_alert_threshold: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None
    is_active: Optional[bool] = None
    is_age_restricted: Optional[bool] = None
    vending_compatible: Optional[bool] = None
    vending_slot: Optional[int] = None


class ProductRead(ProductBase):
    """Schema for reading product (includes DB fields)"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# LINE ITEM SCHEMAS
# ================================================================

class LineItemBase(BaseModel):
    """Base line item fields"""
    product_id: UUID
    quantity: int = Field(default=1, ge=1, description="Number of units")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(..., ge=0, description="Final line price")
    notes: Optional[str] = None


class LineItemCreate(BaseModel):
    """Schema for adding item to cart (simplified)"""
    product_id: UUID
    quantity: int = Field(default=1, ge=1)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    notes: Optional[str] = None


class LineItemRead(LineItemBase):
    """Schema for reading line item"""
    id: UUID
    transaction_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# TRANSACTION SCHEMAS
# ================================================================

class TransactionBase(BaseModel):
    """Base transaction fields"""
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating new transaction (open cart)"""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating transaction"""
    status: Optional[TransactionStatus] = None
    payment_method: Optional[PaymentMethod] = None
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class CheckoutRequest(BaseModel):
    """Schema for checkout (payment processing)"""
    payment_method: PaymentMethod
    amount_tendered: Optional[Decimal] = Field(None, ge=0, description="For cash payments")


class TransactionRead(TransactionBase):
    """Schema for reading transaction"""
    id: UUID
    transaction_number: str
    cashier_id: UUID
    customer_id: Optional[UUID]
    status: TransactionStatus
    payment_method: Optional[PaymentMethod]
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_tendered: Optional[Decimal]
    change_given: Optional[Decimal]
    receipt_number: Optional[str]
    receipt_pdf_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    # Don't load line_items by default (causes async issues)
    # line_items: list[LineItemRead] = []

    model_config = ConfigDict(from_attributes=True)


class TransactionWithItems(TransactionRead):
    """Transaction with line items loaded"""
    line_items: list[LineItemRead] = []


# ================================================================
# SCAN/BARCODE SCHEMAS
# ================================================================

class BarcodeScanRequest(BaseModel):
    """Schema for barcode scan request"""
    barcode: str = Field(..., min_length=1, max_length=100, description="Scanned barcode")
    quantity: int = Field(default=1, ge=1, description="Quantity to add")


class BarcodeScanResponse(BaseModel):
    """Schema for barcode scan response"""
    success: bool
    message: str
    product: Optional[ProductRead] = None
    line_item: Optional[LineItemRead] = None


# ================================================================
# DAILY SUMMARY SCHEMAS (for Felix's email)
# ================================================================

class DailySummary(BaseModel):
    """Daily sales summary for Banana export"""
    date: str
    total_transactions: int
    total_sales: Decimal
    cash_total: Decimal
    visa_total: Decimal
    debit_total: Decimal
    twint_total: Decimal
    crypto_total: Decimal
    other_total: Decimal
    top_seller: Optional[str] = None
    top_seller_quantity: Optional[int] = None
    cashier_performance: dict[str, Decimal] = Field(default_factory=dict)


# ================================================================
# STORE SETTINGS SCHEMAS
# ================================================================

class StoreSettingsBase(BaseModel):
    """Base store settings fields"""
    store_number: int = Field(..., ge=1, description="Store number (1, 2, 3...)")
    store_name: str = Field(..., max_length=255, description="Display name")
    is_active: bool = Field(default=True, description="Is store operational")

    # Company Information
    legal_name: str = Field(..., max_length=255, description="Legal business name")
    address_line1: str = Field(..., max_length=255, description="Street address")
    address_line2: Optional[str] = Field(None, max_length=255, description="Additional address")
    city: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(default="Switzerland", max_length=100)

    # Contact Information
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)

    # Swiss VAT Information
    vat_number: str = Field(..., max_length=50, description="Swiss VAT number")
    vat_rate: Decimal = Field(default=Decimal("8.1"), ge=0, le=100, description="VAT rate percentage")

    # Receipt Settings
    receipt_header: Optional[str] = Field(None, max_length=500)
    receipt_footer: Optional[str] = Field(None, max_length=500)
    receipt_logo_url: Optional[str] = Field(None, max_length=500)

    # Discount Settings
    cashier_max_discount: Decimal = Field(default=Decimal("10.0"), ge=0, le=100)
    manager_max_discount: Decimal = Field(default=Decimal("100.0"), ge=0, le=100)

    # Customer Loyalty Settings
    loyalty_tier1_threshold: Decimal = Field(default=Decimal("0.00"), ge=0)
    loyalty_tier1_discount: Decimal = Field(default=Decimal("10.0"), ge=0, le=100)
    loyalty_tier2_threshold: Decimal = Field(default=Decimal("1000.00"), ge=0)
    loyalty_tier2_discount: Decimal = Field(default=Decimal("15.0"), ge=0, le=100)
    loyalty_tier3_threshold: Decimal = Field(default=Decimal("5000.00"), ge=0)
    loyalty_tier3_discount: Decimal = Field(default=Decimal("25.0"), ge=0, le=100)


class StoreSettingsCreate(StoreSettingsBase):
    """Schema for creating new store settings"""
    pass


class StoreSettingsUpdate(BaseModel):
    """Schema for updating store settings (all fields optional)"""
    store_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    legal_name: Optional[str] = Field(None, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    vat_number: Optional[str] = Field(None, max_length=50)
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    receipt_header: Optional[str] = Field(None, max_length=500)
    receipt_footer: Optional[str] = Field(None, max_length=500)
    receipt_logo_url: Optional[str] = Field(None, max_length=500)
    cashier_max_discount: Optional[Decimal] = Field(None, ge=0, le=100)
    manager_max_discount: Optional[Decimal] = Field(None, ge=0, le=100)
    loyalty_tier1_threshold: Optional[Decimal] = Field(None, ge=0)
    loyalty_tier1_discount: Optional[Decimal] = Field(None, ge=0, le=100)
    loyalty_tier2_threshold: Optional[Decimal] = Field(None, ge=0)
    loyalty_tier2_discount: Optional[Decimal] = Field(None, ge=0, le=100)
    loyalty_tier3_threshold: Optional[Decimal] = Field(None, ge=0)
    loyalty_tier3_discount: Optional[Decimal] = Field(None, ge=0, le=100)


class StoreSettingsRead(StoreSettingsBase):
    """Schema for reading store settings"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
