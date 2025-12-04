# File: src/schemas/headshop_cafe_schema.py
"""
Pydantic schemas for HelixCAFE + HeadShop.
Fast nickels. PAM Cappos. B Chuck's Couch.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class ProductCategoryEnum(str, Enum):
    CBD = "cbd"
    COFFEE = "coffee"
    ACCESSORIES = "accessories"
    BOOKS = "books"
    SNACKS = "snacks"
    MERCH = "merch"


class CBDTypeEnum(str, Enum):
    OIL = "oil"
    DROPS = "drops"
    GUMMIES = "gummies"
    TOPICAL = "topical"
    FLOWER = "flower"
    VAPE = "vape"
    EDIBLE = "edible"


class CBDStrengthEnum(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    STRONG = "strong"
    EXTRA = "extra"


class CoffeeTypeEnum(str, Enum):
    ESPRESSO = "espresso"
    DOUBLE_ESPRESSO = "double_espresso"
    AMERICANO = "americano"
    CAPPUCCINO = "cappuccino"
    LATTE = "latte"
    PAM_CAPPO = "pam_cappo"
    PAM_CAPPO_CBD = "pam_cappo_cbd"
    FLAT_WHITE = "flat_white"
    MOCHA = "mocha"
    TEA = "tea"
    HOT_CHOCOLATE = "hot_chocolate"


class BLQFlavorEnum(str, Enum):
    BLUE = "blue"
    PINEAPPLE = "pineapple"
    NATURAL = "natural"
    MINT = "mint"
    BERRY = "berry"


class MembershipTierEnum(str, Enum):
    GUEST = "guest"
    REGULAR = "regular"
    JACK_BOX = "jack_box"
    VIP = "vip"
    FOUNDER = "founder"


class AccessoryTypeEnum(str, Enum):
    PAPERS = "papers"
    FILTERS = "filters"
    GRINDER = "grinder"
    PIPE = "pipe"
    BONG = "bong"
    VAPORIZER = "vaporizer"
    STORAGE = "storage"
    LIGHTER = "lighter"
    TRAY = "tray"
    OTHER = "other"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ================================================================
# CBD PRODUCT SCHEMAS
# ================================================================

class CBDProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    cbd_type: CBDTypeEnum
    strength: CBDStrengthEnum = CBDStrengthEnum.MEDIUM
    cbd_percentage: Optional[float] = Field(None, ge=0, le=100)
    thc_percentage: Optional[float] = Field(None, ge=0, le=1)
    flavor: Optional[BLQFlavorEnum] = None
    size_ml: Optional[float] = Field(None, ge=0)
    size_grams: Optional[float] = Field(None, ge=0)
    sell_price: float = Field(..., ge=0)
    member_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


class CBDProductCreate(CBDProductBase):
    cost_price: Optional[float] = Field(None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)


class CBDProductRead(CBDProductBase):
    id: UUID
    cost_price: Optional[float] = None
    stock_quantity: int
    low_stock_threshold: int
    lab_tested: bool
    is_active: bool
    is_featured: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CAFE MENU SCHEMAS
# ================================================================

class CafeMenuItemBase(BaseModel):
    name: str = Field(..., max_length=100)
    coffee_type: Optional[CoffeeTypeEnum] = None
    category: ProductCategoryEnum = ProductCategoryEnum.COFFEE
    price: float = Field(..., ge=0)
    member_price: Optional[float] = Field(None, ge=0)
    has_cbd_option: bool = False
    cbd_upcharge: float = Field(default=2.00, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    is_signature: bool = False


class CafeMenuItemCreate(CafeMenuItemBase):
    pass


class CafeMenuItemRead(CafeMenuItemBase):
    id: UUID
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# ACCESSORY SCHEMAS
# ================================================================

class AccessoryBase(BaseModel):
    name: str = Field(..., max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    accessory_type: AccessoryTypeEnum
    sell_price: float = Field(..., ge=0)
    member_price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)


class AccessoryCreate(AccessoryBase):
    cost_price: Optional[float] = Field(None, ge=0)
    stock_quantity: int = Field(default=0, ge=0)


class AccessoryRead(AccessoryBase):
    id: UUID
    stock_quantity: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# MEMBERSHIP SCHEMAS
# ================================================================

class MemberBase(BaseModel):
    name: str = Field(..., max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    nickname: Optional[str] = Field(None, max_length=50)
    tier: MembershipTierEnum = MembershipTierEnum.REGULAR
    favorite_coffee: Optional[CoffeeTypeEnum] = None
    favorite_cbd_flavor: Optional[BLQFlavorEnum] = None
    notes: Optional[str] = None


class MemberCreate(MemberBase):
    customer_id: Optional[UUID] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    nickname: Optional[str] = Field(None, max_length=50)
    tier: Optional[MembershipTierEnum] = None
    favorite_coffee: Optional[CoffeeTypeEnum] = None
    favorite_cbd_flavor: Optional[BLQFlavorEnum] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MemberRead(MemberBase):
    id: UUID
    customer_id: Optional[UUID] = None
    member_since: datetime
    expires_at: Optional[datetime] = None
    jack_box_access: bool
    couch_priority: bool
    discount_percentage: int
    free_cbd_drops: int
    total_visits: int
    total_spent: float
    last_visit: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# ORDER SCHEMAS
# ================================================================

class OrderItemCreate(BaseModel):
    item_name: str = Field(..., max_length=200)
    item_type: str = Field(..., max_length=50)
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(..., ge=0)
    has_cbd: bool = False
    cbd_flavor: Optional[BLQFlavorEnum] = None
    notes: Optional[str] = Field(None, max_length=200)


class OrderItemRead(OrderItemCreate):
    id: UUID
    total_price: float

    model_config = ConfigDict(from_attributes=True)


class CafeOrderCreate(BaseModel):
    member_id: Optional[UUID] = None
    customer_name: Optional[str] = Field(None, max_length=100)
    items: list[OrderItemCreate] = Field(..., min_length=1)
    payment_method: Optional[str] = Field(None, max_length=20)


class CafeOrderRead(BaseModel):
    id: UUID
    member_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    order_number: int
    subtotal: float
    discount: float
    total: float
    paid: bool
    payment_method: Optional[str] = None
    status: str
    items: list[OrderItemRead]
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK ORDER - Fast Nickels
# ================================================================

class QuickCoffeeOrder(BaseModel):
    """Quick order for regular coffee - one click"""
    coffee_type: CoffeeTypeEnum
    add_cbd: bool = False
    cbd_flavor: Optional[BLQFlavorEnum] = None
    member_id: Optional[UUID] = None
    customer_name: Optional[str] = None


class QuickOrderResponse(BaseModel):
    """Quick order response"""
    order_id: UUID
    order_number: int
    item: str
    total: float
    status: str = "preparing"


# ================================================================
# STATS
# ================================================================

class CafeStats(BaseModel):
    """Daily cafe statistics"""
    orders_today: int
    revenue_today: float
    coffees_sold: int
    cbd_products_sold: int
    top_item: str
    member_visits: int
    average_order_value: float


class MembershipStats(BaseModel):
    """Membership overview"""
    total_members: int
    active_today: int
    by_tier: dict[str, int]
    new_this_month: int
