# File: src/schemas/inventory_schema.py
"""
Pydantic schemas for HelixINVENTORY.
Be water. Flow like a river.
Damn capsules need a SYSTEM.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class StockStatusEnum(str, Enum):
    OK = "ok"
    LOW = "low"
    CRITICAL = "critical"
    OUT = "out"
    OVERSTOCKED = "overstocked"


class MovementTypeEnum(str, Enum):
    IN_PURCHASE = "in_purchase"
    IN_RETURN = "in_return"
    IN_ADJUSTMENT = "in_adjustment"
    OUT_SALE = "out_sale"
    OUT_WASTE = "out_waste"
    OUT_SAMPLE = "out_sample"
    OUT_ADJUSTMENT = "out_adjustment"
    TRANSFER = "transfer"


class ReorderStatusEnum(str, Enum):
    SUGGESTED = "suggested"
    APPROVED = "approved"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class SupplierTypeEnum(str, Enum):
    COFFEE = "coffee"
    CBD = "cbd"
    FOOD = "food"
    PET = "pet"
    ACCESSORIES = "accessories"
    GENERAL = "general"


class UnitTypeEnum(str, Enum):
    PIECE = "piece"
    BOX = "box"
    PACK = "pack"
    BOTTLE = "bottle"
    BAG = "bag"
    KG = "kg"
    LITER = "liter"
    CAPSULE = "capsule"


# ================================================================
# SUPPLIER SCHEMAS
# ================================================================

class SupplierBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    supplier_type: SupplierTypeEnum = SupplierTypeEnum.GENERAL
    contact_name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    min_order_amount: Optional[float] = Field(None, ge=0)
    lead_time_days: int = Field(default=1, ge=0)
    is_emergency: bool = False
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# INVENTORY ITEM SCHEMAS
# ================================================================

class InventoryItemBase(BaseModel):
    name: str = Field(..., max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    category: str = Field(..., max_length=50)
    unit_type: UnitTypeEnum = UnitTypeEnum.PIECE
    units_per_pack: int = Field(default=1, ge=1)
    reorder_point: int = Field(default=10, ge=0)
    critical_point: int = Field(default=3, ge=0)
    max_stock: int = Field(default=100, ge=1)
    reorder_quantity: int = Field(default=20, ge=1)
    cost_price: Optional[float] = Field(None, ge=0)
    sell_price: Optional[float] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=100)
    track_inventory: bool = True
    auto_reorder: bool = False


class InventoryItemCreate(InventoryItemBase):
    supplier_id: Optional[UUID] = None
    supplier_sku: Optional[str] = Field(None, max_length=50)
    quantity_on_hand: int = Field(default=0, ge=0)


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    reorder_point: Optional[int] = Field(None, ge=0)
    critical_point: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=1)
    reorder_quantity: Optional[int] = Field(None, ge=1)
    cost_price: Optional[float] = Field(None, ge=0)
    sell_price: Optional[float] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=100)
    supplier_id: Optional[UUID] = None
    track_inventory: Optional[bool] = None
    auto_reorder: Optional[bool] = None
    is_active: Optional[bool] = None


class InventoryItemRead(InventoryItemBase):
    id: UUID
    supplier_id: Optional[UUID] = None
    supplier_sku: Optional[str] = None
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    stock_status: StockStatusEnum
    last_counted: Optional[datetime] = None
    last_ordered: Optional[datetime] = None
    last_received: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryItemWithSupplier(InventoryItemRead):
    primary_supplier: Optional[SupplierRead] = None


# ================================================================
# STOCK MOVEMENT SCHEMAS
# ================================================================

class StockMovementCreate(BaseModel):
    """Record a stock movement - in or out"""
    item_id: UUID
    movement_type: MovementTypeEnum
    quantity: int = Field(..., description="Positive for IN, negative for OUT")
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    unit_cost: Optional[float] = Field(None, ge=0)
    performed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class StockMovementRead(BaseModel):
    id: UUID
    item_id: UUID
    movement_type: MovementTypeEnum
    quantity: int
    quantity_before: int
    quantity_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# REORDER REQUEST SCHEMAS
# ================================================================

class ReorderRequestCreate(BaseModel):
    item_id: UUID
    quantity_requested: int = Field(..., ge=1)
    supplier_id: Optional[UUID] = None
    trigger_reason: str = Field(default="manual", max_length=100)
    notes: Optional[str] = None


class ReorderRequestUpdate(BaseModel):
    status: Optional[ReorderStatusEnum] = None
    quantity_received: Optional[int] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    expected_at: Optional[datetime] = None
    approved_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ReorderRequestRead(BaseModel):
    id: UUID
    item_id: UUID
    supplier_id: Optional[UUID] = None
    quantity_requested: int
    quantity_received: int
    status: ReorderStatusEnum
    trigger_reason: str
    stock_at_trigger: int
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    suggested_at: datetime
    approved_at: Optional[datetime] = None
    ordered_at: Optional[datetime] = None
    expected_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK ACTIONS - Fast Flows
# ================================================================

class QuickStockIn(BaseModel):
    """Quick stock in - Aldi run just arrived"""
    item_id: UUID
    quantity: int = Field(..., ge=1)
    supplier_code: Optional[str] = Field(None, max_length=20)
    cost_per_unit: Optional[float] = Field(None, ge=0)
    performed_by: str = Field(default="Andy", max_length=100)
    notes: Optional[str] = None


class QuickStockOut(BaseModel):
    """Quick stock out - sale or usage"""
    item_id: UUID
    quantity: int = Field(..., ge=1)
    reason: MovementTypeEnum = MovementTypeEnum.OUT_SALE
    performed_by: str = Field(default="Andy", max_length=100)
    notes: Optional[str] = None


class QuickWaste(BaseModel):
    """Michel used the whole bottle again"""
    item_id: UUID
    quantity: int = Field(..., ge=1)
    reason: str = Field(..., max_length=200)
    performed_by: str = Field(default="Michel", max_length=100)


# ================================================================
# DASHBOARD & ALERTS
# ================================================================

class StockAlert(BaseModel):
    """Single stock alert"""
    item_id: UUID
    item_name: str
    category: str
    current_quantity: int
    reorder_point: int
    status: StockStatusEnum
    suggested_order_qty: int
    supplier_name: Optional[str] = None


class InventoryDashboard(BaseModel):
    """Andy's morning dashboard"""
    total_items: int
    items_ok: int
    items_low: int
    items_critical: int
    items_out: int
    alerts: list[StockAlert]
    pending_reorders: int
    recent_movements: list[StockMovementRead]


class CategorySummary(BaseModel):
    """Stock summary by category"""
    category: str
    total_items: int
    total_value: float
    items_needing_reorder: int


class InventoryStats(BaseModel):
    """Inventory statistics"""
    categories: list[CategorySummary]
    total_stock_value: float
    items_tracked: int
    auto_reorder_enabled: int
    movements_today: int
    movements_this_week: int


# ================================================================
# SEARCH & FILTER
# ================================================================

class InventorySearch(BaseModel):
    """Search inventory"""
    query: Optional[str] = None
    category: Optional[str] = None
    status: Optional[StockStatusEnum] = None
    supplier_id: Optional[UUID] = None
    needs_reorder: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


# ================================================================
# CAPSULE SYSTEM - Andy's Special Need
# ================================================================

class CapsuleStatus(BaseModel):
    """Special status just for capsules because Andy needs a SYSTEM"""
    ristretto_count: int
    lungo_count: int
    other_count: int
    total_capsules: int
    status: StockStatusEnum
    days_until_empty: int
    needs_order: bool
    suggested_order: int
    last_order_date: Optional[datetime] = None


class CapsuleOrder(BaseModel):
    """Quick capsule order"""
    ristretto_qty: int = Field(default=0, ge=0)
    lungo_qty: int = Field(default=0, ge=0)
    other_types: Optional[dict[str, int]] = None
    rush_order: bool = False
    notes: Optional[str] = None
