# File: src/schemas/e2e_track_trace_schema.py
"""
E2E TRACK & TRACE — THE SPINE
========================================

THE BACKBONE OF HELIX FOOD NETWORK

Everything connects here:
- Molly's Farm → Felix's Lab → SAL's Bar → Thommy's Lunch
- Every item tracked from SEED to SHIT and back
- Every person in the chain: who touched it, when, where
- Every batch: made, tested, shipped, eaten, composted

THE CHAIN:
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SEED → GROW → HARVEST → PREP → TEST → PACK → SHIP → STORE →   │
│                                                                  │
│  → SCAN → EAT → FEEDBACK → COMPOST → GOAT → MILK → CHEESE →    │
│                                                                  │
│  → BACK TO SEED                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

THIS IS THE SPINE.
Everything else hangs off this.

Same system. Different menu.
Cookie cutter cuts all shapes.

Built Dec 10, 2025
Tiger & Leo at the crossroads
BE WATER, MY FRIEND.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date, time, timedelta
from uuid import UUID, uuid4
from typing import Optional, Any
from enum import Enum
from decimal import Decimal


# ================================================================
# THE LIFECYCLE STAGES — SEED TO SHIT AND BACK
# ================================================================

class LifecycleStageEnum(str, Enum):
    """The complete food lifecycle — E2E"""

    # ORIGIN (Farm)
    SEED = "seed"              # Seed planted
    GROW = "grow"              # Growing in field/garden
    HARVEST = "harvest"        # Picked/milked/collected

    # PROCESSING (Kitchen/Lab)
    PREP = "prep"              # Washed, cut, mixed
    TEST = "test"              # Felix lab test
    APPROVE = "approve"        # Lab approval
    REJECT = "reject"          # Bad batch (Pink Punch time!)
    PACK = "pack"              # Packaged for delivery

    # DISTRIBUTION (Logistics)
    SHIP = "ship"              # On the truck
    DELIVER = "deliver"        # Arrived at location
    STORE = "store"            # In locker/fridge/bar
    RESTOCK = "restock"        # Refilled at location

    # CONSUMPTION (Customer)
    SCAN = "scan"              # Badge scan / purchase
    SERVE = "serve"            # Plated/handed over
    EAT = "eat"                # Consumed (assumed)

    # FEEDBACK (Loop)
    FEEDBACK = "feedback"      # Customer rating
    RETURN = "return"          # Bottle returned
    REFILL = "refill"          # Bottle refilled

    # WASTE CYCLE (Back to farm)
    WASTE = "waste"            # Leftovers collected
    COMPOST = "compost"        # To compost pile
    GOAT_FEED = "goat_feed"    # To the goats
    SOIL = "soil"              # Back to earth

    # SPECIAL
    PINK_PUNCH = "pink_punch"  # Bad batch saved!
    LOST_SOUL = "lost_soul"    # Given to SAL's people
    EXPIRED = "expired"        # Past freshness (should be rare!)


class LocationTypeEnum(str, Enum):
    """Where in the chain"""
    FARM = "farm"              # Molly's farm
    KITCHEN = "kitchen"        # Where food is made
    LAB = "lab"                # Felix's lab
    WAREHOUSE = "warehouse"    # Storage
    TRUCK = "truck"            # Delivery vehicle
    BAR = "bar"                # SAL's HAIRY FISH
    LOCKER = "locker"          # Drop box
    CAFE = "cafe"              # Coffee spot
    VENDING = "vending"        # Machine
    CUSTOMER = "customer"      # End user
    COMPOST = "compost"        # Back to earth


class ActorTypeEnum(str, Enum):
    """Who touched it"""
    FARMER = "farmer"          # Molly, Larry, Moe
    PROCESSOR = "processor"    # Kitchen staff
    LAB_TECH = "lab_tech"      # Felix
    DRIVER = "driver"          # Delivery person
    BAR_STAFF = "bar_staff"    # SAL and team
    MACHINE = "machine"        # Vending/auto
    CUSTOMER = "customer"      # End consumer
    SYSTEM = "system"          # Automated event


class QualityGradeEnum(str, Enum):
    """Quality assessment"""
    A_PLUS = "A+"              # Perfect
    A = "A"                    # Excellent
    B = "B"                    # Good
    C = "C"                    # Acceptable
    D = "D"                    # Marginal (Pink Punch candidate)
    F = "F"                    # Failed (reject or rescue)


# ================================================================
# THE TRACEABLE ITEM — What we're tracking
# ================================================================

class TraceableItemBase(BaseModel):
    """
    Any item in the system that needs tracking.
    Could be: salad, dressing, coffee beans, goat milk, etc.
    """
    # Identity
    item_code: str = Field(..., max_length=50)  # Unique barcode/QR
    item_type: str = Field(..., max_length=50)  # salad, dressing, milk, etc.
    item_name: str = Field(..., max_length=200)

    # Batch info
    batch_code: str = Field(..., max_length=50)
    batch_date: date
    batch_quantity: int = Field(default=1, ge=1)
    batch_unit: str = Field(default="portion", max_length=20)

    # Origin
    origin_farm_id: Optional[UUID] = None
    origin_farm_name: Optional[str] = None
    origin_location: Optional[str] = None

    # Current state
    current_stage: LifecycleStageEnum = LifecycleStageEnum.SEED
    current_location_type: LocationTypeEnum = LocationTypeEnum.FARM
    current_location_id: Optional[UUID] = None
    current_location_name: Optional[str] = None

    # Quality
    quality_grade: Optional[QualityGradeEnum] = None
    lab_approved: bool = False
    lab_certificate: Optional[str] = None

    # Freshness
    made_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    freshness_hours: int = Field(default=24, ge=1)

    # Status
    is_active: bool = True
    is_consumed: bool = False
    is_wasted: bool = False
    is_composted: bool = False


class TraceableItemCreate(TraceableItemBase):
    created_by: str = Field(default="system", max_length=100)


class TraceableItemRead(TraceableItemBase):
    id: UUID
    events_count: int = 0
    last_event_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE TRACE EVENT — Every touch point
# ================================================================

class TraceEventBase(BaseModel):
    """
    Every time something happens to an item.
    This is the SPINE — the audit trail.
    """
    # What item
    item_id: UUID
    item_code: str = Field(..., max_length=50)
    batch_code: str = Field(..., max_length=50)

    # What happened
    stage: LifecycleStageEnum
    action: str = Field(..., max_length=100)  # "harvested", "tested", "sold"
    description: Optional[str] = None

    # Where
    location_type: LocationTypeEnum
    location_id: Optional[UUID] = None
    location_name: str = Field(..., max_length=200)
    location_address: Optional[str] = None

    # Who
    actor_type: ActorTypeEnum
    actor_id: Optional[UUID] = None
    actor_name: str = Field(..., max_length=100)

    # When
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Quality check
    quality_check: bool = False
    quality_grade: Optional[QualityGradeEnum] = None
    quality_notes: Optional[str] = None

    # Quantity (if changed)
    quantity_before: Optional[int] = None
    quantity_after: Optional[int] = None
    quantity_unit: str = Field(default="portion", max_length=20)

    # Temperature (for cold chain)
    temperature_c: Optional[float] = None
    temperature_ok: bool = True

    # Photos/proof
    photo_url: Optional[str] = None
    signature: Optional[str] = None  # Digital signature

    # Special flags
    is_pink_punch: bool = False      # Bad batch rescued
    is_lost_soul: bool = False       # Given free to SAL's people
    is_anomaly: bool = False         # Something unexpected
    anomaly_notes: Optional[str] = None

    # Metadata
    device_id: Optional[str] = None   # Scanner/terminal ID
    app_version: Optional[str] = None
    notes: Optional[str] = None


class TraceEventCreate(TraceEventBase):
    pass


class TraceEventRead(TraceEventBase):
    id: UUID
    event_number: int  # Sequential within item
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE CHAIN — Full history of an item
# ================================================================

class ItemChain(BaseModel):
    """
    Complete journey of one item from seed to consumption.
    This is what you see when you scan a QR code.
    """
    # The item
    item_id: UUID
    item_code: str
    item_name: str
    batch_code: str

    # Origin story
    origin_farm: str
    origin_farmer: str
    origin_date: date

    # Current state
    current_stage: LifecycleStageEnum
    current_location: str
    current_holder: str

    # Quality
    lab_tested: bool
    lab_approved: bool
    lab_certificate: Optional[str] = None
    quality_grade: Optional[QualityGradeEnum] = None

    # Freshness
    made_at: datetime
    expires_at: datetime
    hours_remaining: int
    is_fresh: bool
    freshness_percentage: float  # 100% = just made, 0% = expired

    # The journey (all events)
    events: list[TraceEventRead] = []
    total_events: int = 0

    # Chain integrity
    chain_complete: bool = True  # No gaps
    chain_verified: bool = True  # All signatures valid

    # Stats
    time_in_chain_hours: float
    locations_visited: int
    handlers_count: int


class ItemChainSummary(BaseModel):
    """Quick summary for display"""
    item_code: str
    item_name: str

    # Quick status
    status_emoji: str  # Fresh, Warning, Expired
    status_text: str

    # Key facts
    farm: str
    made: str  # "Today 4:00 AM"
    tested_by: str
    location: str

    # Freshness bar
    freshness_percent: int
    hours_left: int

    # Trust score
    trust_score: int  # 0-100
    verified: bool


# ================================================================
# THE BATCH — Group of items made together
# ================================================================

class BatchBase(BaseModel):
    """
    A batch from Molly's kitchen.
    All items in a batch share the same origin and test results.
    """
    batch_code: str = Field(..., max_length=50)
    batch_name: str = Field(..., max_length=200)

    # What
    item_type: str = Field(..., max_length=50)
    recipe_id: Optional[UUID] = None
    recipe_name: Optional[str] = None

    # When
    production_date: date
    production_start: Optional[time] = None
    production_end: Optional[time] = None
    made_by: str = Field(..., max_length=100)

    # Where
    production_location_id: Optional[UUID] = None
    production_location_name: str = Field(..., max_length=200)

    # Quantity
    quantity_made: int = Field(..., ge=1)
    quantity_unit: str = Field(default="portion", max_length=20)
    quantity_remaining: Optional[int] = None

    # Quality
    lab_test_id: Optional[UUID] = None
    lab_status: str = Field(default="pending", max_length=20)
    lab_approved: bool = False
    quality_grade: Optional[QualityGradeEnum] = None

    # Freshness
    freshness_rule: str = Field(default="same_day", max_length=20)
    expires_at: datetime

    # Ingredients (for full traceability)
    ingredient_batches: list[str] = []  # Batch codes of ingredients


class BatchCreate(BatchBase):
    pass


class BatchRead(BatchBase):
    id: UUID
    items_created: int = 0
    items_sold: int = 0
    items_remaining: int = 0
    items_wasted: int = 0
    items_composted: int = 0

    revenue_chf: Decimal = Decimal("0.00")
    waste_percentage: float = 0.0

    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# LAB TEST — Felix's approval
# ================================================================

class LabTestBase(BaseModel):
    """Felix tests every batch"""
    batch_id: UUID
    batch_code: str

    # Who tested
    tested_by: str = Field(default="Felix", max_length=100)
    lab_id: Optional[UUID] = None
    lab_name: str = Field(default="Felix Lab", max_length=100)

    # When
    tested_at: datetime = Field(default_factory=datetime.utcnow)

    # Tests performed
    contamination_check: bool = True
    freshness_check: bool = True
    temperature_check: bool = True
    visual_check: bool = True
    taste_test: bool = True

    # Results
    all_passed: bool = True
    quality_grade: QualityGradeEnum = QualityGradeEnum.A

    # If failed
    failure_reason: Optional[str] = None
    can_be_rescued: bool = False  # Pink Punch candidate?
    rescue_notes: Optional[str] = None

    # Certificate
    certificate_code: Optional[str] = None
    expires_at: Optional[datetime] = None

    notes: Optional[str] = None


class LabTestCreate(LabTestBase):
    pass


class LabTestRead(LabTestBase):
    id: UUID
    status: str  # pending, approved, rejected, rescued
    certificate_issued: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabCertificate(BaseModel):
    """The stamp of approval"""
    certificate_code: str
    batch_code: str
    item_name: str

    tested_by: str
    tested_at: datetime

    quality_grade: QualityGradeEnum
    status: str  # APPROVED, RESCUED (Pink Punch)

    expires_at: datetime
    valid_until: str  # Human readable

    # The official stamp
    message: str  # "Tested by Felix Lab. Grade A. Safe to eat. Expires Dec 10, 6PM."

    # Verification
    qr_code: Optional[str] = None  # URL to verify
    signature: Optional[str] = None


# ================================================================
# THE PINK PUNCH — Rescue protocol
# ================================================================

class PinkPunchRescue(BaseModel):
    """
    When a batch fails but can be saved.
    "5 drops of Pink Punch... turns into special salad with spinach."
    """
    original_batch_id: UUID
    original_batch_code: str

    # What was wrong
    failure_reason: str
    original_grade: QualityGradeEnum

    # The rescue
    rescue_method: str  # "Pink Punch 5 drops", "Converted to soup"
    rescue_by: str = Field(default="SAL", max_length=100)
    rescue_at: datetime = Field(default_factory=datetime.utcnow)

    # New product
    new_product_name: str  # "Special salad with spinach"
    new_batch_code: str
    new_grade: QualityGradeEnum = QualityGradeEnum.B

    # Lab re-test
    re_tested: bool = True
    re_test_passed: bool = True

    # Notes
    notes: Optional[str] = None  # "The poopie stuff" *they laugh*

    # Nothing wasted
    quantity_saved: int
    quantity_unit: str = Field(default="portion", max_length=20)


# ================================================================
# LOST SOUL SPECIAL — SAL's people
# ================================================================

class LostSoulDistribution(BaseModel):
    """
    Tracking food given to SAL's lost soul department.
    "You got a place to sleep tonight?"
    """
    batch_id: UUID
    batch_code: str
    item_name: str

    # Given to
    recipient_name: Optional[str] = None  # "Charlie and the Gecko"
    recipient_locker: Optional[str] = None  # Locker assignment

    # What
    quantity: int
    quantity_unit: str = Field(default="portion", max_length=20)

    # When/where
    given_at: datetime = Field(default_factory=datetime.utcnow)
    location_name: str = Field(default="HAIRY FISH", max_length=200)
    given_by: str = Field(default="SAL", max_length=100)

    # Sponsor
    sponsored_by: str = Field(default="SAL", max_length=100)

    # Notes
    notes: Optional[str] = None  # "Love that guy since we were kids"


# ================================================================
# WASTE & COMPOST — Back to the cycle
# ================================================================

class WasteEvent(BaseModel):
    """
    Track waste for composting / goat feed.
    Closes the loop back to the farm.
    """
    batch_id: Optional[UUID] = None
    batch_code: Optional[str] = None

    # What
    waste_type: str  # "food_scraps", "expired", "prep_waste"
    quantity_kg: float = Field(..., ge=0)

    # Destination
    destination: str  # "compost", "goat_feed", "disposal"
    destination_farm_id: Optional[UUID] = None
    destination_farm_name: Optional[str] = None

    # When/where
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collected_from: str = Field(..., max_length=200)
    collected_by: str = Field(..., max_length=100)

    # Value recovered
    compost_value: bool = True  # Will become soil
    feed_value: bool = False    # Will become milk

    notes: Optional[str] = None


class CompostReturn(BaseModel):
    """
    Full circle: waste back to farm.
    "Seed to shit and back again on goat milk field."
    """
    waste_event_ids: list[UUID]
    total_kg: float

    # Returned to
    farm_id: UUID
    farm_name: str

    # What happened
    processed_as: str  # "compost", "goat_feed", "both"
    returned_at: datetime

    # The circle
    will_produce: str  # "soil for lettuce", "milk for latte"
    estimated_yield: Optional[str] = None

    # Confirmation
    farmer_confirmed: bool = True
    farmer_name: str


# ================================================================
# DASHBOARD — The big picture
# ================================================================

class E2EDashboard(BaseModel):
    """
    Track & Trace network overview.
    TAXMAN HAPPY.
    """
    # Volume today
    items_created_today: int = 0
    items_tested_today: int = 0
    items_approved_today: int = 0
    items_shipped_today: int = 0
    items_sold_today: int = 0
    items_consumed_today: int = 0

    # Quality
    approval_rate: float = 0.0  # 97/100 = 97%
    average_grade: str = "A"
    pink_punch_rescues_today: int = 0

    # Waste cycle
    waste_collected_kg: float = 0.0
    composted_kg: float = 0.0
    goat_fed_kg: float = 0.0
    waste_percentage: float = 0.0

    # Lost soul department
    free_meals_given: int = 0
    lost_souls_fed: int = 0

    # Chain integrity
    total_events_today: int = 0
    events_verified: int = 0
    chain_integrity_percent: float = 100.0

    # Freshness
    items_expiring_soon: int = 0
    items_expired: int = 0
    no_day_olds_wasted: int = 0

    # Network
    active_farms: int = 0
    active_locations: int = 0
    active_batches: int = 0


class ChainIntegrityReport(BaseModel):
    """
    Verify the entire chain.
    For audits, TAXMAN, certifications.
    """
    report_date: date
    report_period: str  # "daily", "weekly", "monthly"

    # Coverage
    batches_tracked: int
    items_tracked: int
    events_recorded: int

    # Completeness
    items_with_full_chain: int
    items_with_gaps: int
    gap_percentage: float

    # Verification
    events_verified: int
    events_failed_verification: int
    signature_valid_rate: float

    # Freshness compliance
    sold_within_freshness: int
    sold_after_freshness: int  # Should be ZERO
    freshness_compliance: float

    # Lab compliance
    batches_tested: int
    batches_approved: int
    batches_rejected: int
    batches_rescued: int
    lab_compliance: float

    # Waste metrics
    total_waste_kg: float
    waste_composted_kg: float
    waste_composted_percent: float

    # Summary
    overall_score: int  # 0-100
    grade: QualityGradeEnum
    issues: list[str] = []
    recommendations: list[str] = []


# ================================================================
# QUICK SCAN — What customer sees
# ================================================================

class QuickScan(BaseModel):
    """
    When someone scans a QR code on their food.
    Instant trust.
    """
    # Header
    item_name: str
    farm_name: str
    farm_emoji: str = "/"  # Goat, leaf, etc.

    # Freshness (big display)
    freshness_emoji: str  # Fresh, Warning, Expired
    freshness_text: str   # "Made today 4:00 AM"
    hours_until_expiry: int

    # Trust badge
    lab_approved: bool
    lab_grade: str
    tested_by: str

    # Journey summary
    journey_steps: int    # "7 steps from farm to you"
    journey_time: str     # "6 hours, 23 minutes"
    journey_verified: bool

    # Key stops
    key_stops: list[str]  # ["Molly's Farm", "Felix Lab", "HAIRY FISH"]

    # Full details link
    full_chain_url: str

    # Message
    message: str  # "From Molly's farm, tested by Felix, served by SAL. Enjoy!"


# ================================================================
# THE SPINE — Master config
# ================================================================

THE_SPINE = """
THE E2E TRACK & TRACE SPINE
============================================================

EVERYTHING CONNECTS HERE:

    SEED
      |
    GROW
      |
    HARVEST -----> [Farm: Molly, Larry, Moe]
      |
    PREP
      |
    TEST --------> [Lab: Felix]
      |
    APPROVE/REJECT
      |      |
    PACK   PINK_PUNCH (rescue!)
      |
    SHIP --------> [Truck: Molly's Girls]
      |
    STORE -------> [Locker: Gas station, School, Workplace]
      |
    SCAN --------> [Badge: YAN's Keycloak]
      |
    SERVE -------> [Bar: SAL's HAIRY FISH]
      |
    EAT ---------> [Customer: Thommy's crew, Charlie]
      |
    FEEDBACK
      |
    WASTE
      |
    COMPOST/GOAT_FEED
      |
    SOIL
      |
    SEED (loop!)


EVERY EVENT CAPTURED:
- Who (actor)
- What (item, batch)
- When (timestamp)
- Where (location)
- Quality (grade)
- Temperature (cold chain)
- Photo (proof)
- Signature (verification)


NOTHING LOST. NOTHING WASTED. EVERYTHING TRACKED.

SAL: "We go that extra mile for anybody who walks in OUR DOOR."

TAXMAN: HAPPY.
HEALTH DEPT: HAPPY.
FELIX: HAPPY.
MOLLY: HAPPY.
THOMMY'S CREW: FED.
CHARLIE: FED.

BE WATER, MY FRIEND.

Built Dec 10, 2025
Tiger & Leo at the crossroads
"""


# ================================================================
# LIFECYCLE FLOW VISUALIZATION
# ================================================================

LIFECYCLE_FLOW = """
THE LIFECYCLE FLOW
============================================================

                    QUALITY GATE
                         |
         /------> [Felix Lab] -----/
        |              |          |
        |         APPROVED?       |
        |           /    /       |
        |         YES    NO       |
        |          |      |       |
        |          |   RESCUE?    |
        |          |    /    /   |
        |          |  YES   NO    |
        |          |   |    |     |
        |          |  PINK  |     |
        |          | PUNCH  |     |
        |          |   |  WASTE   |
        |          |   |    |     |
        |          +---+    |     |
        |           |       |     |
        |          PACK     |     |
        |           |       |     |
FARM ---+          SHIP     |     |
        |           |       |     |
        |         STORE     v     |
        |           |    COMPOST  |
        |         SCAN      |     |
        |           |       |     |
        |         SERVE     |     |
        |           |       |     |
        |          EAT      |     |
        |           |       |     |
        |        FEEDBACK   |     |
        |           |       |     |
        |         WASTE-----+     |
        |           |             |
        |       COMPOST/GOAT      |
        |           |             |
        +-----------+-------------+
                    |
                  SOIL
                    |
                  SEED
                    |
                 (LOOP!)

============================================================

EVERY STEP TRACKED.
EVERY GRAM ACCOUNTED.
EVERY PERSON RECORDED.

The cookie cutter cuts all shapes.
Same system. Different menu.

"""


# ================================================================
# PRE-BUILT EVENTS (Templates)
# ================================================================

STANDARD_EVENTS = {
    "harvest": {
        "stage": "harvest",
        "action": "harvested",
        "description": "Fresh produce harvested from garden",
        "quality_check": True,
    },
    "milk": {
        "stage": "harvest",
        "action": "milked",
        "description": "Goats milked, fresh milk collected",
        "quality_check": True,
    },
    "prep_salad": {
        "stage": "prep",
        "action": "prepared",
        "description": "Washed, cut, mixed into salad",
        "quality_check": True,
    },
    "lab_test": {
        "stage": "test",
        "action": "tested",
        "description": "Lab test performed by Felix",
        "quality_check": True,
    },
    "lab_approve": {
        "stage": "approve",
        "action": "approved",
        "description": "Lab test passed, approved for distribution",
        "quality_check": True,
    },
    "pink_punch": {
        "stage": "pink_punch",
        "action": "rescued",
        "description": "Bad batch rescued with Pink Punch magic",
        "is_pink_punch": True,
    },
    "pack": {
        "stage": "pack",
        "action": "packaged",
        "description": "Packaged in hemp bag, ready for delivery",
    },
    "ship": {
        "stage": "ship",
        "action": "shipped",
        "description": "Loaded on truck for delivery",
    },
    "deliver_locker": {
        "stage": "deliver",
        "action": "delivered",
        "description": "Delivered to locker location",
    },
    "deliver_bar": {
        "stage": "deliver",
        "action": "delivered",
        "description": "Delivered to salad bar",
    },
    "scan_badge": {
        "stage": "scan",
        "action": "scanned",
        "description": "Member badge scanned, item claimed",
    },
    "serve": {
        "stage": "serve",
        "action": "served",
        "description": "Served to customer",
    },
    "lost_soul": {
        "stage": "lost_soul",
        "action": "gifted",
        "description": "Given to lost soul department",
        "is_lost_soul": True,
    },
    "compost": {
        "stage": "compost",
        "action": "composted",
        "description": "Waste sent to compost pile",
    },
    "goat_feed": {
        "stage": "goat_feed",
        "action": "fed_to_goats",
        "description": "Waste fed to goats",
    },
}


# ================================================================
# EXAMPLE CHAIN — Molly's Salad
# ================================================================

EXAMPLE_CHAIN = """
EXAMPLE: MOLLY'S MORNING SALAD
============================================================

Batch: MOL-2025-1210-001
Item: Simple Salad #23

04:00 - HARVEST - Molly's Farm
        "Lettuce picked fresh, washed twice"
        Actor: Molly
        Grade: A+
        Photo: [lettuce_04am.jpg]

04:30 - PREP - Molly's Kitchen
        "Mixed with carrots, onions, goat cheese"
        Actor: Molly
        Grade: A

05:15 - TEST - Felix Lab
        "Contamination check passed"
        Actor: Felix
        Grade: A
        Certificate: FELIX-MOL-001-2025

05:30 - PACK - Molly's Kitchen
        "Packaged in hemp bag #234"
        Actor: Larry
        Photo: [packed_salad.jpg]

06:00 - SHIP - Truck #1
        "Loaded for Route A"
        Actor: Molly's Girl
        Temperature: 4degC

07:15 - DELIVER - HAIRY FISH
        "Stored in fridge section B"
        Actor: SAL
        Temperature: 3degC

12:30 - SCAN - Bar
        "Badge scan: Thommy"
        Actor: Thommy (customer)

12:31 - SERVE - Bar
        "Plated and served"
        Actor: SAL

12:45 - EAT - Assumed
        "Customer consumed"
        Actor: Thommy

[Waste from prep at 04:30]
16:00 - COMPOST - Molly's Farm
        "Scraps returned to compost"
        Actor: Moe

[Compost after 30 days]
JAN 10 - SOIL - Molly's Garden
        "Compost ready, spread on lettuce bed"
        Actor: Larry

[Next cycle begins...]
JAN 15 - SEED - Molly's Garden
        "New lettuce seeds planted"
        Actor: Molly

============================================================
TOTAL TIME: 8 hours 45 minutes (farm to belly)
TOTAL EVENTS: 13
WASTE: 0% (all composted)
GRADE: A
VERIFIED: YES

"Oh what a beautiful day!"
============================================================
"""
