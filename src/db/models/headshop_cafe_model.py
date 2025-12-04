# File: src/db/models/headshop_cafe_model.py
"""
HelixCAFE + HeadShop Model
"Better fast nickels than slow dimes" - The LEO Way

HEAD SHOP + CAFE + BOOKSTORE
Pet wash is the side hustle. THIS is the main event.

B Chuck's Couch. Jack in the Box. PAM Cappos with CBD.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


# ================================================================
# ENUMS - The Menu Categories
# ================================================================

class ProductCategory(enum.Enum):
    """Main product categories"""
    CBD = "cbd"
    COFFEE = "coffee"
    ACCESSORIES = "accessories"
    BOOKS = "books"
    SNACKS = "snacks"
    MERCH = "merch"


class CBDType(enum.Enum):
    """CBD product types"""
    OIL = "oil"
    DROPS = "drops"
    GUMMIES = "gummies"
    TOPICAL = "topical"
    FLOWER = "flower"
    VAPE = "vape"
    EDIBLE = "edible"


class CBDStrength(enum.Enum):
    """CBD strength levels"""
    LIGHT = "light"         # 5-10%
    MEDIUM = "medium"       # 10-20%
    STRONG = "strong"       # 20-30%
    EXTRA = "extra"         # 30%+


class CoffeeType(enum.Enum):
    """Coffee menu items"""
    ESPRESSO = "espresso"
    DOUBLE_ESPRESSO = "double_espresso"
    AMERICANO = "americano"
    CAPPUCCINO = "cappuccino"
    LATTE = "latte"
    PAM_CAPPO = "pam_cappo"             # Signature series
    PAM_CAPPO_CBD = "pam_cappo_cbd"     # With 2 drops BLQ
    FLAT_WHITE = "flat_white"
    MOCHA = "mocha"
    TEA = "tea"
    HOT_CHOCOLATE = "hot_chocolate"


class BLQFlavor(enum.Enum):
    """BLQ CBD flavors for PAM Cappo"""
    BLUE = "blue"
    PINEAPPLE = "pineapple"
    NATURAL = "natural"
    MINT = "mint"
    BERRY = "berry"


class MembershipTier(enum.Enum):
    """Membership levels"""
    GUEST = "guest"             # Walk-in, no perks
    REGULAR = "regular"         # Basic member
    JACK_BOX = "jack_box"       # Jack in the Box access
    VIP = "vip"                 # B Chuck's Couch priority
    FOUNDER = "founder"         # Day one crew


class AccessoryType(enum.Enum):
    """Head shop accessories"""
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


# ================================================================
# CBD PRODUCT MODEL
# ================================================================

class CBDProductModel(Base):
    """
    CBD products for the head shop.

    BLQ flavors. Swiss quality. Fast nickels.
    """
    __tablename__ = 'cbd_products'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Product Identity
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    sku: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="BLQ, etc"
    )

    # CBD Details
    cbd_type: Mapped[CBDType] = mapped_column(
        SQLEnum(CBDType),
        nullable=False
    )
    strength: Mapped[CBDStrength] = mapped_column(
        SQLEnum(CBDStrength),
        default=CBDStrength.MEDIUM
    )
    cbd_percentage: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="CBD % content"
    )
    thc_percentage: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="THC % (must be < 1% for Swiss legal)"
    )
    flavor: Mapped[BLQFlavor | None] = mapped_column(
        SQLEnum(BLQFlavor),
        nullable=True
    )

    # Sizing
    size_ml: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Volume in ml"
    )
    size_grams: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Weight in grams"
    )

    # Pricing - Fast Nickels
    cost_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    sell_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    member_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Discounted price for members"
    )

    # Inventory
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer,
        default=5
    )

    # Details
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredients: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    lab_tested: Mapped[bool] = mapped_column(Boolean, default=True)
    lab_report_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<CBDProductModel(name='{self.name}', type='{self.cbd_type.value}', price={self.sell_price})>"


# ================================================================
# CAFE MENU MODEL
# ================================================================

class CafeMenuItemModel(Base):
    """
    Cafe menu items.

    PAM Cappos. Double espressos. The good stuff.
    """
    __tablename__ = 'cafe_menu_items'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Item Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    coffee_type: Mapped[CoffeeType | None] = mapped_column(
        SQLEnum(CoffeeType),
        nullable=True
    )
    category: Mapped[ProductCategory] = mapped_column(
        SQLEnum(ProductCategory),
        default=ProductCategory.COFFEE
    )

    # CBD Add-on
    has_cbd_option: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Can add CBD drops"
    )
    cbd_upcharge: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=2.00,
        comment="Extra for CBD version"
    )
    default_cbd_flavor: Mapped[BLQFlavor | None] = mapped_column(
        SQLEnum(BLQFlavor),
        nullable=True
    )

    # Pricing
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    member_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # Details
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ingredients: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_signature: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="PAM Cappo signature series"
    )

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    available_from: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Time like '08:00'"
    )
    available_until: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Time like '18:00'"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<CafeMenuItemModel(name='{self.name}', price={self.price})>"


# ================================================================
# ACCESSORY MODEL - Head Shop Items
# ================================================================

class AccessoryModel(Base):
    """
    Head shop accessories.

    Papers, grinders, pipes. The essentials.
    """
    __tablename__ = 'accessories'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accessory_type: Mapped[AccessoryType] = mapped_column(
        SQLEnum(AccessoryType),
        nullable=False
    )

    # Pricing
    cost_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    sell_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    member_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Inventory
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=3)

    # Details
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    material: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<AccessoryModel(name='{self.name}', type='{self.accessory_type.value}')>"


# ================================================================
# MEMBERSHIP MODEL - Jack in the Box Club
# ================================================================

class MemberModel(Base):
    """
    Membership for the cafe/headshop.

    Jack in the Box = free book access
    VIP = B Chuck's Couch priority
    """
    __tablename__ = 'members'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Link to customer if exists
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Member Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nickname: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="What we call them"
    )

    # Membership
    tier: Mapped[MembershipTier] = mapped_column(
        SQLEnum(MembershipTier),
        default=MembershipTier.REGULAR
    )
    member_since: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Null = never expires"
    )

    # Perks
    jack_box_access: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Can read Jack in the Box books"
    )
    couch_priority: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="B Chuck's Couch priority"
    )
    discount_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Member discount %"
    )
    free_cbd_drops: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Free CBD drops per month"
    )

    # Stats
    total_visits: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    last_visit: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Preferences
    favorite_coffee: Mapped[CoffeeType | None] = mapped_column(
        SQLEnum(CoffeeType),
        nullable=True
    )
    favorite_cbd_flavor: Mapped[BLQFlavor | None] = mapped_column(
        SQLEnum(BLQFlavor),
        nullable=True
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Andy's notes - what they like"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<MemberModel(name='{self.name}', tier='{self.tier.value}')>"


# ================================================================
# CAFE ORDER MODEL - Fast Nickels
# ================================================================

class CafeOrderModel(Base):
    """
    Quick cafe orders.

    Fast nickels > slow dimes.
    """
    __tablename__ = 'cafe_orders'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Customer (optional)
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('members.id', ondelete='SET NULL'),
        nullable=True
    )
    customer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="For walk-ins"
    )

    # Order Details
    order_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Daily order number"
    )

    # Totals
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    # Payment
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="cash, card, twint"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="pending, preparing, ready, completed"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    items: Mapped[list["CafeOrderItemModel"]] = relationship(
        "CafeOrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CafeOrderModel(#{self.order_number}, total={self.total})>"


class CafeOrderItemModel(Base):
    """Individual items in a cafe order"""
    __tablename__ = 'cafe_order_items'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafe_orders.id', ondelete='CASCADE'),
        nullable=False
    )

    # Item
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="coffee, cbd, accessory, book"
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # CBD Add-on
    has_cbd: Mapped[bool] = mapped_column(Boolean, default=False)
    cbd_flavor: Mapped[BLQFlavor | None] = mapped_column(
        SQLEnum(BLQFlavor),
        nullable=True
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Extra hot, no sugar, etc"
    )

    # Relationship
    order: Mapped["CafeOrderModel"] = relationship(
        "CafeOrderModel",
        back_populates="items"
    )

    def __repr__(self):
        return f"<CafeOrderItemModel(name='{self.item_name}', qty={self.quantity})>"


# ================================================================
# DEFAULT MENU - The Starting Lineup
# ================================================================

DEFAULT_COFFEE_MENU = [
    {"name": "Espresso", "coffee_type": CoffeeType.ESPRESSO, "price": 3.50},
    {"name": "Double Espresso", "coffee_type": CoffeeType.DOUBLE_ESPRESSO, "price": 4.50},
    {"name": "Americano", "coffee_type": CoffeeType.AMERICANO, "price": 4.50},
    {"name": "Cappuccino", "coffee_type": CoffeeType.CAPPUCCINO, "price": 5.00},
    {"name": "Latte", "coffee_type": CoffeeType.LATTE, "price": 5.50},
    {
        "name": "PAM Cappo",
        "coffee_type": CoffeeType.PAM_CAPPO,
        "price": 6.00,
        "is_signature": True,
        "description": "Signature series. The good stuff."
    },
    {
        "name": "PAM Cappo + CBD",
        "coffee_type": CoffeeType.PAM_CAPPO_CBD,
        "price": 8.00,
        "is_signature": True,
        "has_cbd_option": True,
        "description": "Signature + 2 drops BLQ. Blue or Pineapple."
    },
    {"name": "Flat White", "coffee_type": CoffeeType.FLAT_WHITE, "price": 5.50},
    {"name": "Mocha", "coffee_type": CoffeeType.MOCHA, "price": 6.00},
    {"name": "Tea", "coffee_type": CoffeeType.TEA, "price": 3.50},
    {"name": "Hot Chocolate", "coffee_type": CoffeeType.HOT_CHOCOLATE, "price": 4.50},
]

DEFAULT_CBD_PRODUCTS = [
    {
        "name": "BLQ Blue Drops",
        "brand": "BLQ",
        "cbd_type": CBDType.DROPS,
        "strength": CBDStrength.MEDIUM,
        "flavor": BLQFlavor.BLUE,
        "sell_price": 35.00,
        "size_ml": 10,
    },
    {
        "name": "BLQ Pineapple Drops",
        "brand": "BLQ",
        "cbd_type": CBDType.DROPS,
        "strength": CBDStrength.MEDIUM,
        "flavor": BLQFlavor.PINEAPPLE,
        "sell_price": 35.00,
        "size_ml": 10,
    },
    {
        "name": "BLQ Natural Oil 10%",
        "brand": "BLQ",
        "cbd_type": CBDType.OIL,
        "strength": CBDStrength.LIGHT,
        "flavor": BLQFlavor.NATURAL,
        "sell_price": 45.00,
        "size_ml": 10,
    },
    {
        "name": "BLQ Strong Oil 20%",
        "brand": "BLQ",
        "cbd_type": CBDType.OIL,
        "strength": CBDStrength.STRONG,
        "flavor": BLQFlavor.NATURAL,
        "sell_price": 65.00,
        "size_ml": 10,
    },
]

DEFAULT_ACCESSORIES = [
    {"name": "RAW Classic Papers", "accessory_type": AccessoryType.PAPERS, "sell_price": 3.00},
    {"name": "RAW Tips", "accessory_type": AccessoryType.FILTERS, "sell_price": 2.00},
    {"name": "Santa Cruz Shredder", "accessory_type": AccessoryType.GRINDER, "sell_price": 45.00},
    {"name": "Clipper Lighter", "accessory_type": AccessoryType.LIGHTER, "sell_price": 3.50},
    {"name": "Rolling Tray Small", "accessory_type": AccessoryType.TRAY, "sell_price": 15.00},
]

MEMBERSHIP_TIERS = {
    MembershipTier.GUEST: {
        "discount": 0,
        "jack_box_access": False,
        "couch_priority": False,
        "free_cbd_drops": 0,
    },
    MembershipTier.REGULAR: {
        "discount": 5,
        "jack_box_access": False,
        "couch_priority": False,
        "free_cbd_drops": 0,
    },
    MembershipTier.JACK_BOX: {
        "discount": 10,
        "jack_box_access": True,
        "couch_priority": False,
        "free_cbd_drops": 2,
    },
    MembershipTier.VIP: {
        "discount": 15,
        "jack_box_access": True,
        "couch_priority": True,
        "free_cbd_drops": 5,
    },
    MembershipTier.FOUNDER: {
        "discount": 20,
        "jack_box_access": True,
        "couch_priority": True,
        "free_cbd_drops": 10,
    },
}
