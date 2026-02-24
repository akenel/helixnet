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
from src.db.models.isotto_invoice_model import IsottoPaymentStatus
from src.db.models.isotto_activity_model import IsottoActivityType
from src.db.models.isotto_catalog_model import IsottoMerchCategory, IsottoPrintMethod
from src.db.models.isotto_order_line_item_model import LineItemStatus
from src.db.models.isotto_purchase_order_model import IsottoPOStatus


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
    # Team order
    is_team_order: bool = False
    team_name: Optional[str] = Field(None, max_length=200)
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
    is_team_order: Optional[bool] = None
    team_name: Optional[str] = Field(None, max_length=200)
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
    is_team_order: bool = False
    team_name: Optional[str] = None
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
# INVOICE SCHEMAS
# ================================================================

class IsottoInvoiceLineItem(BaseModel):
    """Single line item in an invoice"""
    description: str = Field(..., max_length=500)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class IsottoInvoiceCreate(BaseModel):
    """Schema for creating an invoice from a completed order"""
    order_id: UUID
    line_items: list[IsottoInvoiceLineItem] = Field(..., min_length=1)
    due_date: date
    deposit_applied: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class IsottoInvoiceUpdate(BaseModel):
    """Schema for updating invoice (payment, notes)"""
    payment_status: Optional[IsottoPaymentStatus] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    deposit_applied: Optional[Decimal] = Field(None, ge=0)


class IsottoInvoiceRead(BaseModel):
    """Schema for reading invoice (includes all DB fields)"""
    id: UUID
    invoice_number: str
    order_id: UUID
    customer_id: UUID
    line_items: list[dict]
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str
    deposit_applied: Decimal
    amount_due: Decimal
    payment_status: IsottoPaymentStatus
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    due_date: date
    pdf_url: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IsottoPaymentRecord(BaseModel):
    """Schema for recording a payment on an invoice"""
    payment_method: str = Field(..., max_length=50, description="contanti, carta, bonifico")
    amount: Optional[Decimal] = Field(None, ge=0, description="Partial payment amount (None = full)")


# ================================================================
# ACTIVITY SCHEMA
# ================================================================

class IsottoOrderActivityRead(BaseModel):
    """Schema for reading order activity trail entries"""
    id: UUID
    order_id: UUID
    activity_type: IsottoActivityType
    actor: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IsottoOrderCommentCreate(BaseModel):
    """Schema for adding a comment to an order"""
    comment: str = Field(..., min_length=1, max_length=2000)


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
    pending_invoices: int = Field(default=0, description="Invoices awaiting payment")
    revenue_this_month: Decimal = Field(default=Decimal("0.00"), description="Revenue from paid invoices this month")


# ================================================================
# SUPPLIER SCHEMAS
# ================================================================

class IsottoSupplierBase(BaseModel):
    """Base supplier fields"""
    name: str = Field(..., max_length=200, description="Supplier name")
    code: str = Field(..., max_length=20, description="Short code: ROLY, FOTL")
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    default_lead_time_days: int = Field(default=14, ge=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    is_preferred: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class IsottoSupplierCreate(IsottoSupplierBase):
    """Schema for creating a new supplier"""
    pass


class IsottoSupplierUpdate(BaseModel):
    """Schema for updating supplier (all fields optional)"""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    default_lead_time_days: Optional[int] = Field(None, ge=0)
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class IsottoSupplierRead(IsottoSupplierBase):
    """Schema for reading supplier"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CATALOG PRODUCT SCHEMAS
# ================================================================

class IsottoCatalogProductBase(BaseModel):
    """Base catalog product fields"""
    supplier_id: UUID
    supplier_product_code: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., max_length=300, description="Product name")
    description: Optional[str] = None
    category: IsottoMerchCategory
    available_colors: Optional[list] = Field(default_factory=list)
    available_sizes: Optional[list] = Field(default_factory=list)
    supplier_unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    retail_base_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    personalization_markup: Decimal = Field(default=Decimal("5.00"), ge=0)
    print_areas: Optional[list] = Field(default_factory=list)
    recommended_print_methods: Optional[list] = Field(default_factory=list)
    lead_time_days: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    has_sample_in_store: bool = False
    is_active: bool = True
    tags: Optional[str] = None


class IsottoCatalogProductCreate(IsottoCatalogProductBase):
    """Schema for creating a catalog product"""
    pass


class IsottoCatalogProductUpdate(BaseModel):
    """Schema for updating catalog product (all fields optional)"""
    supplier_id: Optional[UUID] = None
    supplier_product_code: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    category: Optional[IsottoMerchCategory] = None
    available_colors: Optional[list] = None
    available_sizes: Optional[list] = None
    supplier_unit_price: Optional[Decimal] = Field(None, ge=0)
    retail_base_price: Optional[Decimal] = Field(None, ge=0)
    personalization_markup: Optional[Decimal] = Field(None, ge=0)
    print_areas: Optional[list] = None
    recommended_print_methods: Optional[list] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    has_sample_in_store: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[str] = None


class IsottoCatalogProductRead(IsottoCatalogProductBase):
    """Schema for reading catalog product"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CATALOG STOCK SCHEMAS
# ================================================================

class IsottoStockEntry(BaseModel):
    """Single stock entry (color + size + quantity)"""
    color: str = Field(..., max_length=50)
    size: str = Field(..., max_length=20)
    quantity_on_hand: int = Field(default=0, ge=0)
    quantity_reserved: int = Field(default=0, ge=0)


class IsottoStockRead(IsottoStockEntry):
    """Stock entry with ID and timestamps"""
    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IsottoStockBulkUpdate(BaseModel):
    """Bulk stock update for a product"""
    entries: list[IsottoStockEntry] = Field(..., min_length=1)


class IsottoStockReceive(BaseModel):
    """Stock receive (increment on delivery)"""
    color: str = Field(..., max_length=50)
    size: str = Field(..., max_length=20)
    quantity: int = Field(..., gt=0, description="Quantity received")


# ================================================================
# ORDER LINE ITEM SCHEMAS
# ================================================================

class IsottoLineItemBase(BaseModel):
    """Base line item fields"""
    catalog_product_id: Optional[UUID] = None
    sort_order: int = Field(default=0, ge=0)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    name_text: Optional[str] = Field(None, max_length=100, description="Name on garment")
    number_text: Optional[str] = Field(None, max_length=10, description="Number on garment")
    custom_text: Optional[str] = Field(None, max_length=500)
    font_name: Optional[str] = Field(None, max_length=100)
    text_color: Optional[str] = Field(None, max_length=50)
    artwork_placement: Optional[str] = Field(None, max_length=50)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class IsottoLineItemCreate(IsottoLineItemBase):
    """Schema for creating a line item"""
    pass


class IsottoLineItemUpdate(BaseModel):
    """Schema for updating a line item (all fields optional)"""
    catalog_product_id: Optional[UUID] = None
    sort_order: Optional[int] = Field(None, ge=0)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    name_text: Optional[str] = Field(None, max_length=100)
    number_text: Optional[str] = Field(None, max_length=10)
    custom_text: Optional[str] = Field(None, max_length=500)
    font_name: Optional[str] = Field(None, max_length=100)
    text_color: Optional[str] = Field(None, max_length=50)
    artwork_placement: Optional[str] = Field(None, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    status: Optional[LineItemStatus] = None
    notes: Optional[str] = None


class IsottoLineItemRead(IsottoLineItemBase):
    """Schema for reading a line item"""
    id: UUID
    order_id: UUID
    status: LineItemStatus
    preview_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IsottoLineItemStatusUpdate(BaseModel):
    """Schema for advancing line item status"""
    status: LineItemStatus


# ================================================================
# ROSTER IMPORT SCHEMA
# ================================================================

class IsottoRosterEntry(BaseModel):
    """A single player/person in a roster import"""
    name_text: str = Field(..., max_length=100, description="Name on garment")
    number_text: Optional[str] = Field(None, max_length=10, description="Number on garment")
    size: str = Field(..., max_length=20, description="Garment size")
    color: Optional[str] = Field(None, max_length=50)
    custom_text: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class IsottoRosterImport(BaseModel):
    """Bulk roster import for team orders"""
    catalog_product_id: Optional[UUID] = Field(None, description="Product for all items (optional)")
    color: Optional[str] = Field(None, max_length=50, description="Default color for all items")
    font_name: Optional[str] = Field(None, max_length=100, description="Default font")
    text_color: Optional[str] = Field(None, max_length=50, description="Default text color")
    artwork_placement: Optional[str] = Field(None, max_length=50, description="Default placement")
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    roster: list[IsottoRosterEntry] = Field(..., min_length=1, description="List of players/people")


# ================================================================
# SIZE SUMMARY SCHEMA
# ================================================================

class IsottoSizeSummaryItem(BaseModel):
    """Aggregated size count with stock comparison"""
    size: str
    count: int = Field(description="Number of items needing this size")
    stock_available: int = Field(default=0, description="Current stock for this size")
    need_to_order: int = Field(default=0, description="Shortfall: count - available")


class IsottoSizeSummary(BaseModel):
    """Size aggregation for an order"""
    order_id: UUID
    total_items: int
    sizes: list[IsottoSizeSummaryItem]
    colors: dict = Field(default_factory=dict, description="Color counts: {'white': 5, 'navy': 3}")


# ================================================================
# PURCHASE ORDER SCHEMAS
# ================================================================

class IsottoPOLineItem(BaseModel):
    """Single line item in a purchase order"""
    product_code: str = Field(..., max_length=100, description="Supplier product code")
    product_name: str = Field(..., max_length=300)
    color: str = Field(..., max_length=50)
    size: str = Field(..., max_length=20)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class IsottoPurchaseOrderBase(BaseModel):
    """Base purchase order fields"""
    supplier_id: UUID
    line_items: list[IsottoPOLineItem] = Field(..., min_length=1)
    expected_delivery: Optional[date] = None
    related_order_ids: Optional[list[UUID]] = Field(default_factory=list)
    notes: Optional[str] = None


class IsottoPurchaseOrderCreate(IsottoPurchaseOrderBase):
    """Schema for creating a purchase order"""
    pass


class IsottoPurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order (all fields optional)"""
    line_items: Optional[list[IsottoPOLineItem]] = None
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    tracking_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[IsottoPOStatus] = None


class IsottoPurchaseOrderRead(BaseModel):
    """Schema for reading a purchase order"""
    id: UUID
    po_number: str
    supplier_id: UUID
    line_items: list[dict]
    subtotal: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    total: Decimal
    currency: str
    status: IsottoPOStatus
    expected_delivery: Optional[date] = None
    actual_delivery: Optional[date] = None
    tracking_number: Optional[str] = None
    related_order_ids: Optional[list] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IsottoPOStatusUpdate(BaseModel):
    """Schema for advancing PO status"""
    status: IsottoPOStatus


class IsottoPOGenerateRequest(BaseModel):
    """Request to auto-generate POs from an order's line items"""
    order_id: UUID


class IsottoPOGenerateResult(BaseModel):
    """Result of PO auto-generation"""
    purchase_orders_created: int
    po_numbers: list[str]
    details: list[dict] = Field(default_factory=list, description="Per-supplier breakdown")


# ================================================================
# ARTWORK SCHEMAS
# ================================================================

class IsottoArtworkBase(BaseModel):
    """Base artwork fields"""
    title: str = Field(..., max_length=200, description="Artwork title")
    customer_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    print_method: Optional[IsottoPrintMethod] = None
    color_count: Optional[int] = Field(None, ge=1)
    width_cm: Optional[Decimal] = Field(None, gt=0)
    height_cm: Optional[Decimal] = Field(None, gt=0)
    is_approved: bool = False
    is_reusable: bool = True
    notes: Optional[str] = None


class IsottoArtworkCreate(IsottoArtworkBase):
    """Schema for creating artwork"""
    pass


class IsottoArtworkUpdate(BaseModel):
    """Schema for updating artwork (all fields optional)"""
    title: Optional[str] = Field(None, max_length=200)
    customer_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    print_method: Optional[IsottoPrintMethod] = None
    color_count: Optional[int] = Field(None, ge=1)
    width_cm: Optional[Decimal] = Field(None, gt=0)
    height_cm: Optional[Decimal] = Field(None, gt=0)
    is_approved: Optional[bool] = None
    is_reusable: Optional[bool] = None
    notes: Optional[str] = None


class IsottoArtworkRead(IsottoArtworkBase):
    """Schema for reading artwork"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
