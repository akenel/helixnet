# File: src/schemas/salad_bar_ecosystem_schema.py
"""
🥗🌿 HELIX SALAD BAR ECOSYSTEM — TONY BOZ CBD EDITION
=====================================================

THE VISION (Electric Dreams Dec 5, 2025):
- Farmers & housewives managing salad bars
- Cannabis fields for JAK
- CBD Salad Dressing — Tony Boz special formulas
- Refillable bottles — NO WASTE
- 5 Francs big coin — TAKE IT OR LEAVE IT
- Salad to go — no time pickup
- CBD Power cream for mouse hand (execs)
- Free stainless steel multi fork/knife — BLQ Swiss camper design
- E2E: Seed to shit and back again on goat milk field
- JURA Coolie hybrid — fresh bean OR Nespresso
- One farmer: goat milk, salad bar, refill
- Large bar to fridge bar — designer collector member plates
- 7 days/week: 4am to 2am

THE PLAYERS:
- SAL: Prototype HAIRY FISH
- FELIX: Artemis expansion
- BORRIS: Event hall, second floor
- FARMERS: Field to table
- HOUSEWIVES: Salad bar managers
- JAK: Cannabis operations
- COOLIE: Coffee hybrid system

TAXMAN HAPPY: Food E2E tracked, seed to sale to soil.

🦁🐅 Built at the crossroads by Tiger & Leo
BE WATER, MY FRIEND.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, time
from uuid import UUID
from typing import Optional
from enum import Enum
from decimal import Decimal


# ================================================================
# ENUMS — THE ECOSYSTEM
# ================================================================

class BarTypeEnum(str, Enum):
    """Types of salad bars in the network"""
    FULL_SERVICE = "full_service"      # SAL's HAIRY FISH style
    SELF_SERVE = "self_serve"          # Weigh plate, tip at end
    FRIDGE_BAR = "fridge_bar"          # Small, grab and go
    TO_GO = "to_go"                    # Pickup only
    VENDING = "vending"                # Machine serve
    EVENT = "event"                    # Borris event hall style


class MembershipTierEnum(str, Enum):
    """Member tiers — signature plates"""
    FISH = "fish"           # Entry level — 🐟
    CAT = "cat"             # Felix tier — 🐱
    TIGER = "tiger"         # Tony Boz — 🐅
    LION = "lion"           # Leo VIP — 🦁
    FOUNDER = "founder"     # Original crew


class ProductCategoryEnum(str, Enum):
    """What we sell"""
    SALAD = "salad"
    DRESSING = "dressing"
    CBD_DRESSING = "cbd_dressing"
    CBD_CREAM = "cbd_cream"
    CBD_POWER = "cbd_power"
    COFFEE = "coffee"
    GOAT_MILK = "goat_milk"
    TO_GO_BOX = "to_go_box"
    UTENSIL = "utensil"
    BOTTLE = "bottle"
    PLATE = "plate"


class SupplyChainStageEnum(str, Enum):
    """E2E: Seed to shit and back"""
    SEED = "seed"
    GROW = "grow"
    HARVEST = "harvest"
    PROCESS = "process"
    PACKAGE = "package"
    DISTRIBUTE = "distribute"
    SERVE = "serve"
    COMPOST = "compost"      # Back to soil
    GOAT_FEED = "goat_feed"  # Waste to goats
    GOAT_MILK = "goat_milk"  # Goats to latte


class RefillStatusEnum(str, Enum):
    """Refillable bottle tracking"""
    NEW = "new"              # First purchase
    REFILLED = "refilled"    # Came back for more
    LOST = "lost"            # Bottle not returned
    DAMAGED = "damaged"      # Needs replacement


# ================================================================
# SALAD BAR LOCATION
# ================================================================

class SaladBarBase(BaseModel):
    """One salad bar in the network"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)  # FISH, ARTEMIS, BORRIS2
    bar_type: BarTypeEnum
    address: str = Field(..., max_length=300)
    manager_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=30)

    # Hours: 4am to 2am, 7 days
    opens_at: time = Field(default=time(4, 0))
    closes_at: time = Field(default=time(2, 0))
    days_open: int = Field(default=7, ge=1, le=7)

    # Capacity
    seats: int = Field(default=0, ge=0)
    bar_length_meters: float = Field(default=2.0, ge=0.5)
    has_fridge_bar: bool = False
    has_coffee_station: bool = False
    has_cbd_section: bool = False


class SaladBarCreate(SaladBarBase):
    owner_id: Optional[UUID] = None


class SaladBarRead(SaladBarBase):
    id: UUID
    owner_id: Optional[UUID] = None
    is_active: bool
    daily_revenue_avg: Optional[Decimal] = None
    members_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# MEMBERSHIP — SIGNATURE PLATES
# ================================================================

class MemberBase(BaseModel):
    """Bar member with signature plate"""
    name: str = Field(..., max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)
    tier: MembershipTierEnum = MembershipTierEnum.FISH
    home_bar_id: Optional[UUID] = None  # Primary bar
    phone: Optional[str] = Field(None, max_length=30)

    # Signature plate
    plate_design: Optional[str] = Field(None, max_length=100)
    plate_number: Optional[int] = None  # Collector number

    # Preferences
    favorite_dressing: Optional[str] = Field(None, max_length=100)
    allergies: Optional[str] = None
    cbd_preference: bool = False


class MemberCreate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: UUID
    visits_total: int = 0
    visits_this_month: int = 0
    refills_count: int = 0
    points: int = 0
    is_active: bool
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CBD PRODUCTS — TONY BOZ SPECIALS
# ================================================================

class CBDProductBase(BaseModel):
    """CBD dressings, creams, powers"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    category: ProductCategoryEnum

    # CBD content
    cbd_percentage: float = Field(default=0.0, ge=0, le=100)
    thc_percentage: float = Field(default=0.0, ge=0, le=1.0)  # Legal limit CH

    # Pricing
    price_chf: Decimal = Field(..., ge=0)
    refill_price_chf: Optional[Decimal] = Field(None, ge=0)  # Cheaper refill

    # Description
    description: Optional[str] = None
    benefits: Optional[str] = None  # "Mouse hand relief"

    # Inventory
    bottle_size_ml: Optional[int] = None
    is_refillable: bool = False


class CBDProductCreate(CBDProductBase):
    supplier_id: Optional[UUID] = None


class CBDProductRead(CBDProductBase):
    id: UUID
    supplier_id: Optional[UUID] = None
    stock_quantity: int = 0
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Tony Boz Specials
TONY_BOZ_CBD_MENU = [
    {
        "name": "Tony Boz Original CBD Dressing",
        "code": "TB-DRESS-OG",
        "category": "cbd_dressing",
        "cbd_percentage": 2.5,
        "price_chf": 12.00,
        "refill_price_chf": 8.00,
        "bottle_size_ml": 250,
        "is_refillable": True,
        "benefits": "Daily wellness, salad enhancement",
    },
    {
        "name": "Tony Boz Power Cream",
        "code": "TB-CREAM-PWR",
        "category": "cbd_power",
        "cbd_percentage": 5.0,
        "price_chf": 25.00,
        "refill_price_chf": 18.00,
        "bottle_size_ml": 100,
        "is_refillable": True,
        "benefits": "Mouse hand, exec stress, joint relief",
    },
    {
        "name": "Tony Boz Sleep Drops",
        "code": "TB-DROP-SLP",
        "category": "cbd_power",
        "cbd_percentage": 10.0,
        "price_chf": 35.00,
        "bottle_size_ml": 30,
        "is_refillable": False,
        "benefits": "Better sleep, no more midnight",
    },
    {
        "name": "Salad Bar CBD Vinaigrette",
        "code": "SB-VIN-CBD",
        "category": "cbd_dressing",
        "cbd_percentage": 1.0,
        "price_chf": 5.00,  # Big coin — take it or leave it
        "refill_price_chf": 3.00,
        "bottle_size_ml": 100,
        "is_refillable": True,
        "benefits": "Light daily dose with your greens",
    },
]


# ================================================================
# REFILLABLE BOTTLE SYSTEM — NO WASTE
# ================================================================

class RefillableBottleBase(BaseModel):
    """Track refillable bottles"""
    bottle_code: str = Field(..., max_length=30)  # QR code on bottle
    product_id: UUID
    member_id: Optional[UUID] = None

    # Status
    status: RefillStatusEnum = RefillStatusEnum.NEW
    refill_count: int = Field(default=0, ge=0)

    # Deposit
    deposit_chf: Decimal = Field(default=Decimal("5.00"))
    deposit_returned: bool = False


class RefillableBottleCreate(RefillableBottleBase):
    pass


class RefillableBottleRead(RefillableBottleBase):
    id: UUID
    first_purchase: datetime
    last_refill: Optional[datetime] = None
    bar_purchased_at: Optional[UUID] = None
    bar_last_refilled_at: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class RefillTransaction(BaseModel):
    """When someone refills their bottle"""
    bottle_id: UUID
    bar_id: UUID
    product_id: UUID
    price_paid: Decimal
    performed_by: str = Field(default="staff", max_length=100)
    notes: Optional[str] = None


# ================================================================
# COFFEE STATION — JURA COOLIE HYBRID
# ================================================================

class CoffeeMachineTypeEnum(str, Enum):
    JURA_FRESH = "jura_fresh"        # Fresh beans
    NESPRESSO = "nespresso"          # Capsules
    COOLIE_HYBRID = "coolie_hybrid"  # Both!
    MANUAL = "manual"


class CoffeeStationBase(BaseModel):
    """JURA Coolie hybrid — fresh bean OR Nespresso"""
    bar_id: UUID
    machine_type: CoffeeMachineTypeEnum = CoffeeMachineTypeEnum.COOLIE_HYBRID
    machine_brand: str = Field(default="JURA", max_length=50)
    machine_model: Optional[str] = Field(None, max_length=50)

    # Options
    has_fresh_beans: bool = True
    has_nespresso: bool = True
    has_goat_milk: bool = False  # From the farm!
    has_oat_milk: bool = True

    # Pricing
    espresso_price: Decimal = Field(default=Decimal("4.50"))
    latte_price: Decimal = Field(default=Decimal("5.50"))
    goat_latte_price: Decimal = Field(default=Decimal("6.50"))


class CoffeeStationRead(CoffeeStationBase):
    id: UUID
    cups_today: int = 0
    last_cleaned: Optional[datetime] = None
    needs_descale: bool = False

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SUPPLY CHAIN — SEED TO SHIT AND BACK
# ================================================================

class FarmBase(BaseModel):
    """Farm in the network — E2E tracking"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    address: str = Field(..., max_length=300)
    farmer_name: str = Field(..., max_length=100)

    # What they produce
    produces_salad_greens: bool = False
    produces_cannabis: bool = False
    produces_goat_milk: bool = False
    produces_eggs: bool = False

    # Goats!
    goat_count: int = Field(default=0, ge=0)

    # Certifications
    is_organic: bool = False
    is_bio_suisse: bool = False


class FarmCreate(FarmBase):
    pass


class FarmRead(FarmBase):
    id: UUID
    bars_supplied: int = 0
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplyChainEvent(BaseModel):
    """Track E2E: seed to shit and back"""
    product_batch: str = Field(..., max_length=50)
    stage: SupplyChainStageEnum
    location_type: str  # farm, processor, bar
    location_id: UUID
    quantity: float
    unit: str = Field(default="kg", max_length=20)
    performed_by: str = Field(..., max_length=100)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    # For compost/goat feed tracking
    waste_to_compost: bool = False
    waste_to_goats: bool = False


# ================================================================
# UTENSILS — BLQ SWISS CAMPER DESIGN
# ================================================================

class UtensilBase(BaseModel):
    """Free stainless steel multi fork/knife"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    design: str = Field(default="BLQ Swiss Camper", max_length=50)

    # Multi-tool
    has_fork: bool = True
    has_knife: bool = True
    has_spoon: bool = False

    # Material
    material: str = Field(default="stainless_steel", max_length=50)
    is_reusable: bool = True

    # Pricing
    cost_chf: Decimal = Field(default=Decimal("0.00"))  # FREE with salad
    deposit_chf: Optional[Decimal] = Field(default=Decimal("2.00"))


class UtensilRead(UtensilBase):
    id: UUID
    given_out_total: int = 0
    returned_total: int = 0
    return_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# SALAD TO GO — NO TIME PICKUP
# ================================================================

class ToGoOrderBase(BaseModel):
    """Quick pickup order"""
    member_id: Optional[UUID] = None
    bar_id: UUID

    # Contents
    salad_weight_grams: int = Field(..., ge=100)
    dressing_id: Optional[UUID] = None
    cbd_add_on: bool = False
    includes_utensil: bool = True

    # Pricing
    total_chf: Decimal

    # Pickup
    pickup_time: Optional[datetime] = None
    is_ready: bool = False
    is_picked_up: bool = False


class ToGoOrderCreate(ToGoOrderBase):
    pass


class ToGoOrderRead(ToGoOrderBase):
    id: UUID
    order_number: str
    created_at: datetime
    picked_up_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# DAILY OPERATIONS — 4AM TO 2AM
# ================================================================

class DailyReportBase(BaseModel):
    """Bar daily report — TAXMAN HAPPY"""
    bar_id: UUID
    date: datetime

    # Revenue
    salad_revenue: Decimal = Field(default=Decimal("0.00"))
    dressing_revenue: Decimal = Field(default=Decimal("0.00"))
    cbd_revenue: Decimal = Field(default=Decimal("0.00"))
    coffee_revenue: Decimal = Field(default=Decimal("0.00"))
    other_revenue: Decimal = Field(default=Decimal("0.00"))
    total_revenue: Decimal = Field(default=Decimal("0.00"))

    # Volume
    salads_served: int = 0
    coffees_served: int = 0
    refills_done: int = 0
    to_go_orders: int = 0

    # Members
    member_visits: int = 0
    new_members: int = 0

    # Waste (for goats!)
    waste_kg: float = 0.0
    waste_to_compost: float = 0.0
    waste_to_goats: float = 0.0


class DailyReportRead(DailyReportBase):
    id: UUID
    submitted_by: str
    submitted_at: datetime
    approved: bool = False
    approved_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# NETWORK DASHBOARD — THE BIG PICTURE
# ================================================================

class NetworkDashboard(BaseModel):
    """All bars at a glance"""
    total_bars: int
    bars_open_now: int

    # Today's numbers
    total_revenue_today: Decimal
    salads_served_today: int
    coffees_served_today: int
    refills_today: int

    # Members
    total_members: int
    active_members_this_month: int

    # Supply chain
    farms_active: int
    goats_in_network: int
    waste_composted_this_month_kg: float

    # Top performers
    top_bar_today: Optional[str] = None
    top_member_today: Optional[str] = None


# ================================================================
# THE 5 FRANC DEAL — TAKE IT OR LEAVE IT
# ================================================================

class FiveFrancDeal(BaseModel):
    """The big coin special"""
    name: str = Field(default="5 Franc Salad Deal")
    price_chf: Decimal = Field(default=Decimal("5.00"))

    includes_salad_grams: int = Field(default=200)
    includes_dressing: bool = True
    includes_fork: bool = True
    cbd_option_extra: Decimal = Field(default=Decimal("2.00"))

    tagline: str = Field(default="TAKE IT OR LEAVE IT")


# ================================================================
# MASTER CONFIG — THE WHOLE ECOSYSTEM
# ================================================================

ECOSYSTEM_CONFIG = {
    "name": "Tony Boz CBD Salad Network",
    "tagline": "BE WATER, MY FRIEND",
    "hours": "4am to 2am, 7 days",

    "principles": [
        "Refillable bottles — NO WASTE",
        "E2E: Seed to shit and back",
        "Goat milk in the latte",
        "BLQ Swiss design",
        "TAXMAN HAPPY",
        "5 Francs — TAKE IT OR LEAVE IT",
    ],

    "membership_tiers": ["fish", "cat", "tiger", "lion", "founder"],

    "signature_products": [
        "Tony Boz Original CBD Dressing",
        "Tony Boz Power Cream (mouse hand)",
        "JURA Coolie Goat Latte",
        "BLQ Multi Fork/Knife",
    ],

    "founders": ["SAL", "FELIX", "BORRIS", "TONY"],

    "built_by": "🦁🐅 Tiger & Leo at the crossroads",
    "philosophy": "BE WATER, MY FRIEND",
}
