# File: src/schemas/farm_to_locker_schema.py
"""
🌻 MOLLY'S FARM TO LOCKER — Fresh Food Chain
=============================================

The Vision:
- Swiss farmers are KILLING themselves
- NWO wants the land (talk to Bill the GATES)
- Construction workers eating ROAD KILL at gas stations
- Mom & pop shops KILLED during COVID

The Solution:
- Molly makes salad LEGAL (farm fresh, tested)
- Felix lab signs off (OK, expires X days)
- Drop boxes like AMAZON but for FOOD
- Lockers for the BUMS (SAL's idea)
- Badge system (YAN has scanner at Luzern school)
- Keycloak gateway — in/out of shops, cafes, laundry
- Marco pumps machines, Borris custom bars
- Track & trace via HELIX

The Chain:
MOLLY (farm) → FELIX (lab test) → DROP BOX → WORKER (grabs)
     ↓              ↓                ↓            ↓
  Fresh          Certified        Ready        FED

No plastic. Eat the wrapper. Hemp bags. No waste.
No day-olds. Super fresh. 5 days a week.

THE FIGHTERS NEED REAL FOOD.
CAN HELIX DO IT? YES.

🦁🐅🌻 Built while people are starving for solutions.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date, time, timedelta
from uuid import UUID
from typing import Optional
from src.core.constants import HelixEnum
from decimal import Decimal


# ================================================================
# ENUMS
# ================================================================

class FarmTypeEnum(HelixEnum):
    """What kind of farm?"""
    DAIRY = "dairy"              # Goat milk, cheese
    VEGETABLE = "vegetable"      # Salad greens, carrots, onions
    FRUIT = "fruit"              # Apples, berries
    MIXED = "mixed"              # Molly's farm — all of it
    HONEY = "honey"              # Bees buzzing
    HERB = "herb"                # CBD, hemp, flowers


class ProductTypeEnum(HelixEnum):
    """What Molly makes"""
    SALAD = "salad"              # The main event
    SOUP = "soup"                # Hot and fresh
    DRESSING = "dressing"        # Molly's secret sauce
    SANDWICH = "sandwich"        # Packed lunch
    DRINK = "drink"              # Pink Punch, milk
    CHEESE = "cheese"            # Farm fresh
    COOKIE = "cookie"            # CBD/Hemp special
    BREAD = "bread"              # Fresh baked
    MILK = "milk"                # Goat milk
    EGGS = "eggs"                # Farm fresh


class PackagingTypeEnum(HelixEnum):
    """No plastic. No waste."""
    HEMP_BAG = "hemp_bag"        # Eat the wrapper
    TIN_FOIL = "tin_foil"        # For now
    GLASS_JAR = "glass_jar"      # Refillable
    PAPER_BOX = "paper_box"      # Compostable
    BANANA_LEAF = "banana_leaf"  # Natural wrap
    BEESWAX_WRAP = "beeswax_wrap"  # Reusable
    EDIBLE = "edible"            # EAT THE WRAPPER


class FreshnessRuleEnum(HelixEnum):
    """No day-olds. Super fresh."""
    SAME_DAY = "same_day"        # Made today, eat today
    NEXT_DAY = "next_day"        # 24 hours max
    THREE_DAY = "three_day"      # 72 hours
    WEEK = "week"                # 7 days (sealed)
    MONTH = "month"              # Preserved/canned


class LabStatusEnum(HelixEnum):
    """Felix signs off"""
    PENDING = "pending"          # Waiting for test
    TESTING = "testing"          # In the lab
    APPROVED = "approved"        # OK — safe to eat
    REJECTED = "rejected"        # Bad batch (Pink Punch it!)
    EXPIRED = "expired"          # Past freshness window


class LockerTypeEnum(HelixEnum):
    """Where the food goes"""
    GAS_STATION = "gas_station"  # Front or back location
    SCHOOL = "school"            # YAN's scanner
    WORKPLACE = "workplace"      # Marco's idea
    CAFE = "cafe"                # Mom & pop
    LAUNDRY = "laundry"          # Why not?
    GYM = "gym"                  # Fitness food
    TRAIN_STATION = "train_station"  # Commuters
    LOST_SOUL = "lost_soul"      # SAL's lockers for the bums


class MemberTierEnum(HelixEnum):
    """Badge levels"""
    WORKER = "worker"            # Construction crew
    REGULAR = "regular"          # Daily customers
    PREMIUM = "premium"          # Subscription
    LOST_SOUL = "lost_soul"      # Free tier (SAL's people)
    FARMER = "farmer"            # Molly's network


# ================================================================
# THE FARM — Molly's Operation
# ================================================================

class FarmBase(BaseModel):
    """A farm in the network"""
    name: str = Field(..., max_length=100)
    farm_type: FarmTypeEnum
    owner_name: str = Field(..., max_length=100)

    # Location
    address: Optional[str] = None
    region: str = Field(default="Swiss Alps", max_length=100)

    # What they produce
    products: list[ProductTypeEnum] = []

    # Certifications
    is_organic: bool = True
    is_local: bool = True
    farm_code: Optional[str] = Field(None, max_length=20)

    # The people
    has_brothers: bool = False  # Molly has big hard-working brothers
    family_farm: bool = True

    # Animals
    has_goats: bool = False     # Goat milk
    has_bees: bool = False      # Honey, buzzing
    has_chickens: bool = False  # Eggs

    notes: Optional[str] = None


class FarmCreate(FarmBase):
    pass


class FarmRead(FarmBase):
    id: UUID
    is_active: bool = True
    products_count: int = 0
    batches_this_week: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE PRODUCT — What Molly Makes
# ================================================================

class FarmProductBase(BaseModel):
    """One product from the farm"""
    name: str = Field(..., max_length=100)
    product_type: ProductTypeEnum
    description: Optional[str] = None

    # Source
    farm_id: UUID
    made_by: str = Field(default="Molly", max_length=100)

    # Freshness rules
    freshness_rule: FreshnessRuleEnum = FreshnessRuleEnum.SAME_DAY
    shelf_life_hours: int = Field(default=24, ge=1)

    # Packaging (no plastic!)
    packaging: PackagingTypeEnum = PackagingTypeEnum.HEMP_BAG
    is_zero_waste: bool = True

    # Nutrition
    calories: int = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)

    # Price
    price_chf: Decimal = Field(..., ge=0, decimal_places=2)

    # Secret ingredient?
    has_secret_sauce: bool = False
    secret_ingredient: Optional[str] = None  # "Goat milk blend"


class FarmProductCreate(FarmProductBase):
    pass


class FarmProductRead(FarmProductBase):
    id: UUID
    lab_status: LabStatusEnum = LabStatusEnum.PENDING
    lab_tested_at: Optional[datetime] = None
    lab_tested_by: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE BATCH — What Molly Made Today
# ================================================================

class BatchBase(BaseModel):
    """A batch from Molly's kitchen"""
    product_id: UUID
    batch_code: str = Field(..., max_length=50)

    # When
    made_date: date
    made_time: Optional[time] = None
    made_by: str = Field(default="Molly", max_length=100)

    # How much
    quantity: int = Field(..., ge=1)
    unit: str = Field(default="portion", max_length=20)

    # Freshness
    freshness_rule: FreshnessRuleEnum
    expires_at: datetime

    # Quality
    quality_notes: Optional[str] = None
    is_good_batch: bool = True  # 17/20 are good, 3/20 need Pink Punch


class BatchCreate(BatchBase):
    pass


class BatchRead(BatchBase):
    id: UUID
    lab_status: LabStatusEnum
    lab_result: Optional[str] = None
    remaining_quantity: int
    is_sold_out: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# FELIX'S LAB — Test & Certify
# ================================================================

class LabTestBase(BaseModel):
    """Felix tests Molly's batch"""
    batch_id: UUID
    tested_by: str = Field(default="Felix", max_length=100)

    # Test results
    is_safe: bool = True
    contamination_check: bool = True  # No dirt on carrots
    freshness_check: bool = True
    taste_test: bool = True

    # Certification
    approved: bool = False
    expiry_date: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None  # "Bad batch — Pink Punch it!"


class LabTestCreate(LabTestBase):
    pass


class LabTestRead(LabTestBase):
    id: UUID
    status: LabStatusEnum
    certificate_code: Optional[str] = None
    tested_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabCertificate(BaseModel):
    """The stamp of approval"""
    certificate_code: str
    batch_id: UUID
    product_name: str
    farm_name: str

    tested_by: str
    tested_at: datetime

    status: str  # "OK — APPROVED"
    expires_at: datetime

    # The stamp
    message: str  # "Tested by Felix Lab. Safe to eat. Expires Dec 10."


# ================================================================
# THE DROP BOX / LOCKER — Like Amazon but for FOOD
# ================================================================

class LockerLocationBase(BaseModel):
    """A locker location in the network"""
    name: str = Field(..., max_length=100)
    locker_type: LockerTypeEnum

    # Where
    address: str = Field(..., max_length=200)
    region: str = Field(default="Luzern", max_length=100)

    # Access
    has_badge_scanner: bool = True  # YAN's system
    has_key_backup: bool = True     # Charlie has a key
    has_code_access: bool = True

    # Partner
    partner_name: Optional[str] = None  # "Shell Gas Station"
    partner_contact: Optional[str] = None

    # Capacity
    total_lockers: int = Field(default=10, ge=1)
    locker_sizes: list[str] = ["small", "medium", "large"]

    # Special
    is_refrigerated: bool = True
    is_heated: bool = False  # For soup

    # Lost soul department
    has_free_lockers: bool = False  # SAL's idea
    free_locker_count: int = Field(default=0, ge=0)

    notes: Optional[str] = None


class LockerLocationCreate(LockerLocationBase):
    pass


class LockerLocationRead(LockerLocationBase):
    id: UUID
    lockers_available: int
    lockers_in_use: int
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SingleLocker(BaseModel):
    """One locker in a location"""
    id: UUID
    location_id: UUID
    locker_number: str = Field(..., max_length=10)  # "A1", "B3"
    size: str = Field(default="medium", max_length=20)

    # Status
    is_available: bool = True
    is_reserved: bool = False
    is_refrigerated: bool = True

    # Current contents
    current_order_id: Optional[UUID] = None
    reserved_for: Optional[str] = None
    reserved_until: Optional[datetime] = None

    # Lost soul special
    is_free_locker: bool = False
    assigned_to_lost_soul: Optional[str] = None  # "Charlie and the Gecko"


# ================================================================
# THE MEMBER — Badge System (Keycloak)
# ================================================================

class MemberBase(BaseModel):
    """A member with a badge"""
    name: str = Field(..., max_length=100)
    badge_code: str = Field(..., max_length=50)  # Scans at gateway
    tier: MemberTierEnum = MemberTierEnum.WORKER

    # Contact
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)

    # Work info
    employer: Optional[str] = None  # "Thommy's Crew"
    work_type: Optional[str] = None  # "Construction"

    # Preferences
    favorite_products: list[str] = []
    allergies: list[str] = []
    hates_tuna: bool = True

    # Subscription
    has_subscription: bool = False
    subscription_type: Optional[str] = None  # "Daily lunch"


class MemberCreate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: UUID
    total_orders: int = 0
    total_spent_chf: Decimal = Decimal("0")
    total_saved_chf: Decimal = Decimal("0")  # vs gas station
    is_active: bool = True
    created_at: datetime
    last_order_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LostSoulMember(BaseModel):
    """SAL's lost soul department"""
    name: str = Field(..., max_length=100)
    badge_code: str = Field(..., max_length=50)

    # Their locker
    assigned_locker_id: Optional[UUID] = None
    locker_location: Optional[str] = None

    # What they get
    free_meals_per_week: int = Field(default=7, ge=0)
    meals_received_this_week: int = Field(default=0, ge=0)

    # Story
    nickname: Optional[str] = None  # "Charlie and the Gecko"
    notes: Optional[str] = None  # "Love that guy since we were kids"

    # Sponsor
    sponsored_by: str = Field(default="SAL", max_length=100)


# ================================================================
# THE ORDER — Farm to Locker Flow
# ================================================================

class LockerOrderBase(BaseModel):
    """An order to a locker"""
    member_id: UUID
    member_name: str

    # What they want
    items: list[UUID]  # Product IDs

    # Where
    locker_location_id: UUID
    locker_number: Optional[str] = None  # Assigned at pickup

    # When
    pickup_date: date
    pickup_time_from: Optional[time] = None
    pickup_time_to: Optional[time] = None

    # Payment
    total_chf: Decimal
    is_paid: bool = False
    is_subscription: bool = False

    notes: Optional[str] = None


class LockerOrderCreate(LockerOrderBase):
    pass


class LockerOrderRead(LockerOrderBase):
    id: UUID
    status: str  # "pending", "preparing", "in_locker", "picked_up", "expired"

    # Locker assignment
    assigned_locker: Optional[str] = None
    access_code: Optional[str] = None  # One-time code

    # Tracking
    prepared_at: Optional[datetime] = None
    delivered_to_locker_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE DELIVERY — Molly's Girls Restock
# ================================================================

class DeliveryRouteBase(BaseModel):
    """A delivery route for restocking"""
    route_name: str = Field(..., max_length=100)
    driver_name: str = Field(default="Molly's Girl", max_length=100)

    # Stops
    locker_locations: list[UUID]

    # Schedule
    days_of_week: list[str]  # ["monday", "tuesday", ...]
    departure_time: time
    estimated_duration_min: int

    # Vehicle
    vehicle_type: str = Field(default="van", max_length=50)
    is_refrigerated: bool = True


class DeliveryRouteRead(DeliveryRouteBase):
    id: UUID
    stops_count: int
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryStop(BaseModel):
    """One stop on the route"""
    route_id: UUID
    locker_location_id: UUID
    location_name: str

    # What to deliver
    orders: list[UUID]
    products_count: int

    # Timing
    estimated_arrival: datetime
    actual_arrival: Optional[datetime] = None

    # Status
    status: str  # "pending", "arrived", "restocked", "complete"
    restocked_by: Optional[str] = None


# ================================================================
# THE TRACK & TRACE — Food Chain via Helix
# ================================================================

class FoodChainEvent(BaseModel):
    """Track every step of the food"""
    event_id: UUID
    batch_id: UUID
    product_name: str

    # The chain
    step: str  # "harvested", "processed", "tested", "packaged", "delivered", "picked_up"
    location: str

    # Who
    performed_by: str

    # When
    timestamp: datetime

    # Details
    notes: Optional[str] = None
    photo_url: Optional[str] = None  # Proof


class FoodChainHistory(BaseModel):
    """Full history of a product"""
    batch_id: UUID
    product_name: str
    farm_name: str

    # The journey
    events: list[FoodChainEvent]

    # Current status
    current_location: str
    current_status: str

    # Freshness
    made_at: datetime
    expires_at: datetime
    hours_remaining: int
    is_fresh: bool


# ================================================================
# THE DASHBOARD — Network Overview
# ================================================================

class FarmToLockerDashboard(BaseModel):
    """The big picture"""
    # Farms
    farms_active: int
    farms_total_products: int

    # Today's production
    batches_today: int
    products_made_today: int
    products_tested_today: int
    products_approved_today: int

    # Locker network
    locker_locations: int
    total_lockers: int
    lockers_in_use: int
    lockers_available: int

    # Lost soul department
    free_lockers_active: int
    lost_souls_fed_today: int

    # Orders
    orders_today: int
    orders_pending: int
    orders_in_locker: int
    orders_picked_up: int

    # Members
    total_members: int
    active_members_today: int

    # Savings vs gas station
    total_saved_today_chf: Decimal
    total_saved_this_week_chf: Decimal

    # Freshness
    products_expiring_soon: int
    no_day_olds_wasted: int  # We don't waste!


# ================================================================
# MOLLY'S SIMPLE LUNCH BOXES — Easy, ISO, Fresh
# ================================================================

MOLLY_LUNCH_BOXES = [
    {
        "name": "Molly's Simple Salad",
        "description": "Farm fresh, same day. No day-olds.",
        "contents": ["Mixed greens", "Farm veggies", "Goat cheese", "Secret dressing"],
        "packaging": "hemp_bag",
        "freshness": "same_day",
        "price_chf": "9.50",
        "calories": 450,
    },
    {
        "name": "Molly's Soup & Bread",
        "description": "Hot soup, fresh bread. Soul food.",
        "contents": ["Daily soup", "Fresh bread roll", "Butter"],
        "packaging": "glass_jar",
        "freshness": "same_day",
        "price_chf": "8.00",
        "calories": 550,
    },
    {
        "name": "Molly's Farmer Box",
        "description": "What the brothers eat. Heavy fuel.",
        "contents": ["Big salad", "Cheese wedge", "Bread", "Eggs (2)", "Apple"],
        "packaging": "paper_box",
        "freshness": "same_day",
        "price_chf": "14.00",
        "calories": 950,
    },
    {
        "name": "CBD Cookie Pack",
        "description": "Hemp cookies for the road. Legal. Tested.",
        "contents": ["CBD cookies (3)", "Honey stick"],
        "packaging": "hemp_bag",
        "freshness": "week",
        "price_chf": "12.00",
        "calories": 350,
    },
    {
        "name": "Lost Soul Special",
        "description": "Free for SAL's people. No questions.",
        "contents": ["Simple salad", "Bread", "Water"],
        "packaging": "paper_box",
        "freshness": "same_day",
        "price_chf": "0.00",
        "calories": 400,
    },
]


# ================================================================
# THE CHAIN — How It All Connects
# ================================================================

THE_FOOD_CHAIN = """
┌─────────────────────────────────────────────────────────────────────┐
│                    MOLLY'S FARM TO LOCKER CHAIN                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  MOLLY'S FARM                                                       │
│  ├─ Goats (milk, cheese)                                           │
│  ├─ Bees (honey, buzzing)                                          │
│  ├─ Garden (veggies, salad)                                        │
│  ├─ Brothers (hard-working farmers)                                │
│  └─ Secret sauce (goat milk blend)                                 │
│         │                                                           │
│         ▼                                                           │
│  MOLLY'S KITCHEN                                                    │
│  ├─ Makes salad, soup, dressing                                    │
│  ├─ Packages in hemp bags (no plastic!)                            │
│  ├─ Logs ISO, timestamps everything                                │
│  └─ Wrap in box, ready for drop                                    │
│         │                                                           │
│         ▼                                                           │
│  FELIX'S LAB                                                        │
│  ├─ Tests every batch                                              │
│  ├─ Signs off: "OK — Expires X days"                               │
│  ├─ Bad batch? Pink Punch it! (no waste)                           │
│  └─ Certificate code for tracking                                  │
│         │                                                           │
│         ▼                                                           │
│  DELIVERY (Molly's Girls)                                          │
│  ├─ Food truck route                                               │
│  ├─ Hits gas stations (doesn't go inside)                          │
│  ├─ Restocks lockers                                               │
│  └─ 5 days a week, super fresh                                     │
│         │                                                           │
│         ▼                                                           │
│  DROP BOX / LOCKER                                                  │
│  ├─ Gas station (front or back)                                    │
│  ├─ Schools (YAN's scanner)                                        │
│  ├─ Workplaces (Marco's idea)                                      │
│  ├─ Cafes, laundry, gyms                                           │
│  └─ Lost Soul lockers (SAL's people)                               │
│         │                                                           │
│         ▼                                                           │
│  MEMBER BADGE SCAN (Keycloak)                                       │
│  ├─ Worker tier (Thommy's crew)                                    │
│  ├─ Regular tier (daily customers)                                 │
│  ├─ Premium tier (subscription)                                    │
│  └─ Lost Soul tier (FREE — SAL sponsors)                           │
│         │                                                           │
│         ▼                                                           │
│  THE WORKER                                                         │
│  ├─ Italian construction guys                                      │
│  ├─ "Grab your SANDs, we got work!"                                │
│  ├─ Real food, not gas station garbage                             │
│  └─ "Oh what a beautiful day!"                                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  TRACK & TRACE (Helix)                                             │
│  ├─ Every step logged                                              │
│  ├─ Batch codes                                                    │
│  ├─ Freshness windows                                              │
│  ├─ No day-olds (all goes or soup)                                 │
│  └─ ISO compliant                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  THE PARTNERS:                                                      │
│  ├─ MOLLY — Farm, kitchen, recipe                                  │
│  ├─ FELIX — Lab, testing, certification                            │
│  ├─ SAL — Lost soul lockers, network                               │
│  ├─ MARCO — Machines, equipment, pumps                             │
│  ├─ BORRIS — Custom salad bars                                     │
│  ├─ YAN — Badge scanner, Keycloak                                  │
│  └─ THOMMY — The customers, the crew                               │
│                                                                     │
│  CAN HELIX DO IT? YES.                                             │
│  CAN WE BUILD IT? WE JUST DID.                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

THE_LOST_SOUL_DEPARTMENT = """
┌─────────────────────────────────────────────────────────────────────┐
│                    SAL'S LOST SOUL DEPARTMENT                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  "You got a place to sleep tonight?" — SAL                         │
│                                                                     │
│  THE LOCKERS:                                                       │
│  ├─ 2 garbage bags (winter & summer clothes)                       │
│  ├─ A key (Charlie has one)                                        │
│  ├─ Backup scan to open                                            │
│  └─ Free meals — no questions                                      │
│                                                                     │
│  WHO QUALIFIES:                                                     │
│  ├─ Anyone SAL says                                                │
│  ├─ No paperwork                                                   │
│  ├─ No judgment                                                    │
│  └─ "Love that guy since we were kids"                             │
│                                                                     │
│  WHAT THEY GET:                                                     │
│  ├─ Lost Soul Special (free)                                       │
│  ├─ Simple salad, bread, water                                     │
│  ├─ 7 meals per week                                               │
│  └─ A place to keep their stuff                                    │
│                                                                     │
│  SPONSORED BY: SAL (and anyone who donates)                        │
│                                                                     │
│  "Here at the FISH it is FREE."                                    │
│  "We go that extra mile for anybody who walks in OUR DOOR."        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

THE_NO_WASTE_PRINCIPLE = """
┌─────────────────────────────────────────────────────────────────────┐
│                     NO WASTE — EAT THE WRAPPER                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PACKAGING:                                                         │
│  ├─ Hemp bags (compostable, edible seed)                           │
│  ├─ Tin foil (recyclable, for now)                                 │
│  ├─ Glass jars (refillable, deposit)                               │
│  ├─ Paper boxes (compostable)                                      │
│  ├─ Beeswax wraps (reusable)                                       │
│  └─ Banana leaf (natural, eat it)                                  │
│                                                                     │
│  NO PLASTIC. EVER.                                                  │
│                                                                     │
│  NO DAY-OLDS:                                                       │
│  ├─ Same day salad → sold or given free                            │
│  ├─ End of day → Lost Soul Special                                 │
│  ├─ Still good? → Soup tomorrow                                    │
│  ├─ Bad batch? → Pink Punch save                                   │
│  └─ NOTHING WASTED                                                 │
│                                                                     │
│  THE CYCLE:                                                         │
│  Food scraps → Compost → Goats → Milk → Cheese → Salad             │
│       ↑                                                    │        │
│       └────────────────────────────────────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""
