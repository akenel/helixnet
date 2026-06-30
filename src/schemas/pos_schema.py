# File: src/schemas/pos_schema.py
"""
Pydantic schemas for POS (Point of Sale) system.
Used for request validation and response serialization.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, Literal
from src.db.models.transaction_model import TransactionStatus, PaymentMethod
from src.db.models.supplier_model import normalize_supplier_prefix
from src.services.vat_resolver import Consumption


# ================================================================
# SUPPLIER REGISTRY SCHEMAS
# A supplier = an import source identified by a unique SKU prefix.
# ================================================================
_ADAPTER_TYPES = ("tamar", "magento", "csv", "manual")


class SupplierCreate(BaseModel):
    """Create a supplier. `prefix` is force-uppercased + validated server-side."""
    prefix: str = Field(..., description="SKU prefix, 2-3 uppercase letters (e.g. TAM, FTW)")
    name: str = Field(..., min_length=1, max_length=100, description="Full supplier name")
    source_url: Optional[str] = Field(None, max_length=500, description="Web origin (sync / 'View on source')")
    adapter_type: Optional[Literal["tamar", "magento", "csv", "manual"]] = Field(
        None, description="Import adapter type"
    )
    contact_name: Optional[str] = Field(None, max_length=120, description="Named contact person (handoff)")
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50, description="Supplier VAT/UID number (handoff)")
    is_active: bool = Field(default=True)

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, v: str) -> str:
        # Uppercases + enforces ^[A-Z]{2,3}$ and the reserved set {ART, LZ}.
        return normalize_supplier_prefix(v)


class SupplierUpdate(BaseModel):
    """Edit / deactivate a supplier. Prefix re-validated only if supplied."""
    prefix: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)
    adapter_type: Optional[Literal["tamar", "magento", "csv", "manual"]] = None
    contact_name: Optional[str] = Field(None, max_length=120)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    vat_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

    @field_validator("prefix")
    @classmethod
    def _check_prefix(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_supplier_prefix(v)


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    prefix: Optional[str] = None
    name: str
    source_url: Optional[str] = None
    adapter_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    vat_number: Optional[str] = None
    is_active: bool = True


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
    is_age_restricted: bool = Field(default=False, description="Requires 18+ ID (derived from product_class)")
    product_class: str = Field(default="standard", max_length=40, description="Behaviour class — drives 18+ + VAT (catalog_taxonomy)")
    vending_compatible: bool = Field(default=False, description="Can be sold via vending machine")
    vending_slot: Optional[int] = Field(None, description="Vending machine slot number")
    # Catalog picture + supplier + reorder fields (BL-88 catalog dashboard / P4 reorder)
    image_url: Optional[str] = Field(None, max_length=500, description="Catalog picture URL")
    supplier_name: Optional[str] = Field(None, max_length=255, description="Supplier")
    min_stock: Optional[int] = Field(None, ge=0, description="Reorder trigger level")
    max_stock: Optional[int] = Field(None, ge=0, description="Reorder up-to level")
    lead_time_days: Optional[int] = Field(None, ge=0, description="Supplier lead time (days)")


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
    product_class: Optional[str] = Field(None, max_length=40)
    vending_compatible: Optional[bool] = None
    vending_slot: Optional[int] = None
    image_url: Optional[str] = Field(None, max_length=500)
    supplier_name: Optional[str] = Field(None, max_length=255)
    min_stock: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)


class ProductRead(ProductBase):
    """Schema for reading product (includes DB fields)"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductSuggestion(BaseModel):
    """AI-drafted product fields from a photo (cashier confirms before saving)."""
    name: str = ""
    brand: str = ""
    category: Optional[str] = None
    size: str = ""
    description: Optional[str] = None
    tags: Optional[str] = None
    price_estimate: Optional[Decimal] = None
    confidence: float = 0.0


class ProductSuggestResponse(BaseModel):
    """Wrapper: the suggestion + which brain answered + how long it took.

    `elapsed_ms` is the AI round-trip — the number we time for the demo KPI.
    `note` is set (and the suggestion blank) when the AI was unavailable, so the
    UI degrades to plain typing instead of erroring.
    """
    suggestion: ProductSuggestion
    provider: str
    model: str = ""
    elapsed_ms: int
    note: Optional[str] = None


# ================================================================
# LINE ITEM SCHEMAS
# ================================================================

class LineItemBase(BaseModel):
    """Base line item fields"""
    product_id: Optional[UUID] = None  # None for custom lines (manual/change)
    quantity: int = Field(default=1, ge=1, description="Number of units")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(..., ge=0, description="Final line price")
    notes: Optional[str] = None


class LineItemCreate(BaseModel):
    """Schema for adding an item to the cart.

    product_id is OPTIONAL: a custom line (manual catalog entry, product-as-change
    treat) has no catalog product -- it carries its own name + unit_price instead.
    For real products the server always prices from the catalog (client unit_price
    is ignored, so it can't be tampered with)."""
    product_id: Optional[UUID] = None
    # Upper cap = fat-finger guard (monkey/fuzz 2026-06-27 accepted qty 10,000,000).
    quantity: int = Field(default=1, ge=1, le=10000)
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    notes: Optional[str] = None
    # Only used for custom lines (product_id is None):
    name: Optional[str] = None
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    # A free promotional treat: real product, zero revenue, stock still leaves.
    is_giveaway: bool = False
    # Cafe multi-line VAT: dine-in (8.1%) vs takeaway (2.6%). Defaults to the safe,
    # legally-conservative dine-in; any value outside the enum is rejected with 422.
    consumption: Consumption = Field(
        default=Consumption.DINE_IN,
        description="dine_in | takeaway -- sets the per-line VAT rate (cafe food/drink)")


class LineItemRead(LineItemBase):
    """Schema for reading line item"""
    id: UUID
    transaction_id: UUID
    created_at: datetime
    # Per-line VAT snapshot (cafe multi-line tax). consumption always present; rate/amount
    # are null on lines rung before this shipped.
    consumption: str = "dine_in"
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None

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
    customer_id: Optional[UUID] = Field(None, description="Loyalty member this sale belongs to (CRM)")


class SaleCreate(BaseModel):
    """Atomic create-sale (P2.1): the WHOLE cart + payment in ONE idempotent request —
    the keystone for the offline outbox and strictly better online (no fragile 3-round-trip
    partial-failure window). `client_uuid` is the idempotency key: replaying the same sale
    (a network retry, or an offline outbox draining on reconnect) adopts it EXACTLY ONCE
    instead of double-ringing. The server prices + taxes authoritatively (same rules as the
    3-step path — catalog price wins, per-line VAT snapshot, promo guard); the client only
    captures intent. `discount_percent` is the cart-wide discount (mirrors the legacy flow,
    where it was echoed on every line); per-line discounts on `lines` are not used here."""
    client_uuid: UUID = Field(..., description="Client idempotency key — replay-safe, adopted once")
    lines: list[LineItemCreate] = Field(..., min_length=1, description="The cart (≥1 line)")
    payment_method: PaymentMethod
    amount_tendered: Optional[Decimal] = Field(None, ge=0, description="For cash payments")
    customer_id: Optional[UUID] = Field(None, description="Loyalty member this sale belongs to (CRM)")
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100,
                                      description="Cart-wide % discount applied once to the total")
    notes: Optional[str] = None


class RefundRequest(BaseModel):
    """Schema for refund/return processing"""
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for refund (e.g., 'Broken item', 'Wrong product')")
    refund_method: str = Field(default="cash", description="How to refund: 'cash' (always cash back) or 'original' (same method)")
    partial_amount: Optional[Decimal] = Field(None, ge=0, description="For partial refunds, specify amount. Full refund if omitted.")


class TransactionRead(TransactionBase):
    """Schema for reading transaction"""
    id: UUID
    transaction_number: str
    cashier_id: UUID
    cashier_name: Optional[str] = None  # BL-83: resolved display name (Pam/Felix/Ralph)
    customer_name: Optional[str] = None  # BL-95: loyalty member the sale was rung under (else blank)
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
# RECEIVING SCHEMAS (BL-91 — stock IN at the counter)
# ================================================================

class ReceivingItem(BaseModel):
    """One line of a goods-in: a known product + how many units arrived."""
    product_id: UUID
    quantity: int = Field(..., ge=1, description="Units received (singles)")


class ReceivingRequest(BaseModel):
    """A goods-in batch: several products received in one go (lean — no PO)."""
    items: list[ReceivingItem] = Field(..., min_length=1)
    reference: Optional[str] = Field(default=None, max_length=140,
                                     description="Optional delivery note / supplier ref")


class ReceivingLineResult(BaseModel):
    product_id: UUID
    name: str
    quantity_received: int
    stock_after: int


class ReceivingResponse(BaseModel):
    success: bool
    received_lines: int
    total_units: int
    lines: list[ReceivingLineResult]


# ================================================================
# DAILY SUMMARY SCHEMAS (for Felix's email)
# ================================================================

class DailySummary(BaseModel):
    """Daily sales summary for Banana export"""
    date: str
    total_transactions: int
    total_sales: Decimal
    vat_total: Decimal = Decimal("0.00")  # VAT contained in the day's gross sales (inclusive)
    # Swiss VAT split (INC3) — the two turnover streams booked apart for the FTA:
    # standard 8.1% (dine-in cafe + retail/alcohol/tobacco) vs reduced 2.6% (takeaway cafe).
    vat_standard: Decimal = Decimal("0.00")
    vat_reduced: Decimal = Decimal("0.00")
    turnover_standard: Decimal = Decimal("0.00")
    turnover_reduced: Decimal = Decimal("0.00")
    cash_total: Decimal
    visa_total: Decimal
    debit_total: Decimal
    twint_total: Decimal
    bank_transfer_total: Decimal = Decimal("0.00")  # BL-84: invoice/IBAN paid to shop account
    crypto_total: Decimal
    other_total: Decimal
    top_seller: Optional[str] = None
    top_seller_quantity: Optional[int] = None
    top_sellers: list[dict] = Field(default_factory=list)   # top 3: [{name, quantity}]
    items_sold: int = 0
    average_sale: Decimal = Decimal("0.00")
    busiest_hour: Optional[str] = None
    cashier_performance: dict[str, Decimal] = Field(default_factory=dict)
    # Promotional treats given free today: count + their cost (COGS, for tax).
    giveaway_count: int = 0
    giveaway_cost: Decimal = Decimal("0.00")


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
    opening_hours: Optional[str] = Field(None, max_length=500)
    facebook_url: Optional[str] = Field(None, max_length=255)
    instagram_url: Optional[str] = Field(None, max_length=255)
    founded_year: Optional[str] = Field(None, max_length=10)

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
    opening_hours: Optional[str] = Field(None, max_length=500)
    facebook_url: Optional[str] = Field(None, max_length=255)
    instagram_url: Optional[str] = Field(None, max_length=255)
    founded_year: Optional[str] = Field(None, max_length=10)
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
