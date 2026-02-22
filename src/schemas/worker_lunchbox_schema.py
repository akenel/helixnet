# File: src/schemas/worker_lunchbox_schema.py
"""
🥪 WORKER'S LUNCH BOX — The Highway Robbery Solution
=====================================================

The Scene:
- Thommy the Gypsy revving up: "Grab your SANDs, we got work!"
- Gas station: 7 francs, ZERO nutrient
- Search search... brown bread? NO. Croissant? Grab anything.
- 4 people paying with last 30 rappen
- Highway robbery prices, LOW value

The Solution:
- Molly's packages (farm fresh, farmer talk)
- Felix's lab (tested, verified)
- SAL's network (distribution)
- Pack at home quality — ready to grab

The Workers:
- 5 sheets drywall = need A, B, C, D vitamins
- Low energy input, HIGH output needed
- Coffee breaks matter
- "Oh what a beautiful day" — Thommy knows the secret

🦁🐅 Built for the hungry tigers on the job.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date, time
from uuid import UUID
from typing import Optional
from src.core.constants import HelixEnum
from decimal import Decimal


# ================================================================
# ENUMS
# ================================================================

class WorkerTypeEnum(HelixEnum):
    """The crew types"""
    CONSTRUCTION = "construction"      # Thommy's drywall crew
    DELIVERY = "delivery"              # On the road all day
    FARM = "farm"                      # Molly's brothers
    WAREHOUSE = "warehouse"            # Loading, lifting
    TRADE = "trade"                    # Electricians, plumbers
    OFFICE = "office"                  # Desk workers (still need fuel)
    EVENT = "event"                    # Long shifts, no breaks


class MealTypeEnum(HelixEnum):
    """When you eat"""
    BREAKFAST = "breakfast"            # Pink Punch time
    MORNING_SNACK = "morning_snack"    # 10:30 coffee break
    LUNCH = "lunch"                    # The main event
    AFTERNOON_SNACK = "afternoon_snack"  # 3pm slump killer
    DINNER = "dinner"                  # Late shift fuel


class EnergyLevelEnum(HelixEnum):
    """How hard you working?"""
    LIGHT = "light"                    # Office, sitting
    MEDIUM = "medium"                  # Walking, light lifting
    HEAVY = "heavy"                    # Construction, farm work
    EXTREME = "extreme"                # 5 sheets drywall, no sleep


class PackageTypeEnum(HelixEnum):
    """How it comes"""
    LUNCHBOX = "lunchbox"              # Full meal pack
    GRAB_GO = "grab_go"                # Quick grab
    SANDWICH = "sandwich"              # The SAND
    SALAD = "salad"                    # Molly's special
    DRINK = "drink"                    # Pink Punch, coffee
    SNACK = "snack"                    # Biberli, energy bar


class NutrientGradeEnum(HelixEnum):
    """The ABCDs — what you NEED"""
    A_PLUS = "a+"                      # Full spectrum, perfect
    A = "a"                            # Excellent nutrition
    B = "b"                            # Good, solid
    C = "c"                            # Acceptable
    D = "d"                            # Barely there
    F = "f"                            # Gas station garbage


class FreshnessEnum(HelixEnum):
    """How fresh?"""
    FARM_FRESH = "farm_fresh"          # Same day from Molly
    MORNING_MADE = "morning_made"      # Made this morning
    YESTERDAY = "yesterday"            # Still good
    PACKAGED = "packaged"              # Sealed, dated
    HIGHWAY_ROBBERY = "highway_robbery"  # Gas station mystery


# ================================================================
# THE LUNCH BOX — What's Inside
# ================================================================

class LunchBoxItemBase(BaseModel):
    """One item in the box"""
    name: str = Field(..., max_length=100)
    category: PackageTypeEnum
    calories: int = Field(..., ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    fiber_g: float = Field(default=0, ge=0)
    sugar_g: float = Field(default=0, ge=0)
    sodium_mg: float = Field(default=0, ge=0)

    # The ABCDs
    vitamin_a_pct: float = Field(default=0, ge=0, le=100)
    vitamin_b_pct: float = Field(default=0, ge=0, le=100)
    vitamin_c_pct: float = Field(default=0, ge=0, le=100)
    vitamin_d_pct: float = Field(default=0, ge=0, le=100)

    freshness: FreshnessEnum = FreshnessEnum.MORNING_MADE
    nutrient_grade: NutrientGradeEnum = NutrientGradeEnum.B

    # Source
    source: Optional[str] = Field(None, max_length=100)  # "Molly's Farm"
    tested_by: Optional[str] = Field(None, max_length=100)  # "Felix Lab"


class LunchBoxItemCreate(LunchBoxItemBase):
    price_chf: Decimal = Field(..., ge=0, decimal_places=2)
    prep_time_min: int = Field(default=0, ge=0)


class LunchBoxItemRead(LunchBoxItemBase):
    id: UUID
    price_chf: Decimal
    prep_time_min: int
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE WORKER PROFILE — Know Your Tiger
# ================================================================

class WorkerProfileBase(BaseModel):
    """Who's eating?"""
    name: str = Field(..., max_length=100)
    worker_type: WorkerTypeEnum
    energy_level: EnergyLevelEnum = EnergyLevelEnum.HEAVY

    # Daily needs based on work
    daily_calories_target: int = Field(default=2500, ge=1000)
    protein_target_g: float = Field(default=100, ge=0)

    # Preferences
    hates_tuna: bool = Field(default=True)  # Felix hates tuna
    vegetarian: bool = False
    allergies: list[str] = []
    favorite_items: list[str] = []

    # Work schedule
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    coffee_break_time: Optional[time] = None  # 10:30 for Thommy's crew


class WorkerProfileCreate(WorkerProfileBase):
    pass


class WorkerProfileRead(WorkerProfileBase):
    id: UUID
    created_at: datetime
    total_orders: int = 0
    favorite_box: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE FULL LUNCH BOX — The Package
# ================================================================

class LunchBoxBase(BaseModel):
    """The complete box — Thommy's dream"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

    # Who it's for
    worker_type: WorkerTypeEnum = WorkerTypeEnum.CONSTRUCTION
    energy_level: EnergyLevelEnum = EnergyLevelEnum.HEAVY
    meal_type: MealTypeEnum = MealTypeEnum.LUNCH

    # What's inside (item IDs)
    items: list[UUID] = []

    # Totals (calculated)
    total_calories: int = Field(default=0, ge=0)
    total_protein_g: float = Field(default=0, ge=0)
    nutrient_grade: NutrientGradeEnum = NutrientGradeEnum.B

    # The value proposition
    price_chf: Decimal = Field(..., ge=0, decimal_places=2)
    gas_station_equivalent_chf: Decimal = Field(default=Decimal("15.00"), ge=0)
    savings_chf: Decimal = Field(default=Decimal("0"), ge=0)

    # Source chain
    made_by: str = Field(default="Molly", max_length=100)
    tested_by: Optional[str] = Field(None, max_length=100)
    freshness: FreshnessEnum = FreshnessEnum.MORNING_MADE


class LunchBoxCreate(LunchBoxBase):
    pass


class LunchBoxRead(LunchBoxBase):
    id: UUID
    created_at: datetime
    times_ordered: int = 0
    rating_avg: float = Field(default=0, ge=0, le=5)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK ORDER — Grab and Go
# ================================================================

class QuickOrder(BaseModel):
    """Thommy honking, no time to browse"""
    worker_id: Optional[UUID] = None
    worker_name: str = Field(default="Hungry Tiger", max_length=100)

    # What you want
    box_id: Optional[UUID] = None  # Pre-made box
    items: list[UUID] = []  # Or pick items

    # Quick options
    add_coffee: bool = True
    coffee_type: str = Field(default="100_calorie", max_length=50)
    add_water: bool = True
    water_with_gas: bool = False

    # Where
    pickup_location: str = Field(default="SAL's Bar", max_length=100)
    pickup_time: Optional[datetime] = None

    notes: Optional[str] = None  # "No tuna!"


class QuickOrderRead(BaseModel):
    id: UUID
    worker_name: str
    items_count: int
    total_calories: int
    total_price_chf: Decimal
    savings_vs_gas_station: Decimal
    pickup_location: str
    pickup_time: Optional[datetime]
    status: str  # "ready", "preparing", "picked_up"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CREW ORDER — Thommy Orders for the Boys
# ================================================================

class CrewMember(BaseModel):
    """One of the boys"""
    name: str = Field(..., max_length=100)
    box_id: Optional[UUID] = None
    custom_items: list[UUID] = []
    special_requests: Optional[str] = None  # "Extra Biberli"


class CrewOrder(BaseModel):
    """Thommy: 'Grab your SANDs boys, we got work!'"""
    crew_leader: str = Field(..., max_length=100)  # Thommy
    crew_name: Optional[str] = Field(None, max_length=100)  # "The Gypsies"

    members: list[CrewMember]

    # Bulk additions
    coffees_count: int = Field(default=0, ge=0)
    waters_count: int = Field(default=0, ge=0)

    # Delivery
    job_site_address: Optional[str] = None
    delivery_time: Optional[datetime] = None
    pickup_location: str = Field(default="SAL's Bar", max_length=100)

    notes: Optional[str] = None


class CrewOrderSummary(BaseModel):
    """What Thommy pays"""
    id: UUID
    crew_leader: str
    crew_size: int
    boxes_count: int
    coffees_count: int
    waters_count: int

    total_calories: int
    total_protein_g: float
    avg_nutrient_grade: str

    total_price_chf: Decimal
    gas_station_would_cost: Decimal
    total_savings_chf: Decimal

    status: str
    pickup_time: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# COFFEE BREAK SPECIAL — 10:30 with the Boys
# ================================================================

class CoffeeBreakOrder(BaseModel):
    """The 10:30 ritual"""
    crew_size: int = Field(..., ge=1)

    # Coffee options
    coffee_100_cal: int = Field(default=0, ge=0)  # Better than Red Bull
    coffee_regular: int = Field(default=0, ge=0)
    pink_punch: int = Field(default=0, ge=0)      # Thommy's favorite

    # Snacks
    biberli_count: int = Field(default=0, ge=0)   # 2 per person standard
    energy_bars: int = Field(default=0, ge=0)

    # Quick bites
    bread_cheese_packs: int = Field(default=0, ge=0)

    pickup_location: str = Field(default="SAL's Bar", max_length=100)
    pickup_time: Optional[time] = None  # 10:30


class CoffeeBreakSummary(BaseModel):
    """Quick total for the break"""
    crew_size: int
    items_count: int
    total_calories: int
    total_price_chf: Decimal
    per_person_chf: Decimal
    ready_at: Optional[time]

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# NUTRITION CALCULATOR — The ABCDs
# ================================================================

class NutritionCheck(BaseModel):
    """Does this box have what a tiger needs?"""
    box_id: UUID
    worker_type: WorkerTypeEnum
    energy_level: EnergyLevelEnum

    # Requirements based on work
    calories_needed: int
    calories_provided: int
    calories_gap: int

    protein_needed_g: float
    protein_provided_g: float
    protein_ok: bool

    # The ABCDs
    vitamin_a_ok: bool
    vitamin_b_ok: bool
    vitamin_c_ok: bool
    vitamin_d_ok: bool

    overall_grade: NutrientGradeEnum
    recommendation: str  # "Add more protein" or "Perfect for heavy work!"


class EnergyRequirements(BaseModel):
    """What you need based on work"""
    worker_type: WorkerTypeEnum
    energy_level: EnergyLevelEnum

    calories_per_day: int
    protein_g_per_day: float
    carbs_g_per_day: float

    recommended_meals: int  # 3 meals + 2 snacks for heavy work
    hydration_liters: float

    sample_day: list[str]  # ["Breakfast: Pink Punch + eggs", "10:30: Coffee + Biberli", ...]


# ================================================================
# THE GAS STATION COMPARISON — Highway Robbery Exposed
# ================================================================

class GasStationItem(BaseModel):
    """What they sell"""
    name: str
    price_chf: Decimal
    calories: int
    nutrient_grade: NutrientGradeEnum = NutrientGradeEnum.F
    actual_value: str  # "ZERO nutrient"


class HighwayRobberyReport(BaseModel):
    """Compare our box to gas station garbage"""
    our_box_name: str
    our_price_chf: Decimal
    our_calories: int
    our_grade: NutrientGradeEnum

    gas_station_equivalent: list[GasStationItem]
    gas_station_total_chf: Decimal
    gas_station_calories: int
    gas_station_grade: NutrientGradeEnum

    you_save_chf: Decimal
    extra_calories: int
    grade_improvement: str  # "F → A"

    verdict: str  # "Our box: Real food. Their box: Highway robbery."


# ================================================================
# DAILY SPECIALS — What Molly Made Today
# ================================================================

class DailySpecial(BaseModel):
    """Fresh from the farm"""
    date: date
    name: str = Field(..., max_length=100)
    description: str

    # Source
    made_by: str = Field(default="Molly", max_length=100)
    source: str = Field(default="Farm fresh", max_length=100)

    # The goods
    items_included: list[str]
    total_calories: int
    nutrient_grade: NutrientGradeEnum

    # Special sauce
    secret_ingredient: Optional[str] = None  # "Goat milk blend"

    price_chf: Decimal
    quantity_available: int

    # Timing
    available_from: time
    available_until: time
    freshness: FreshnessEnum = FreshnessEnum.FARM_FRESH


class WeeklyMenu(BaseModel):
    """What's cooking this week"""
    week_start: date
    week_end: date

    specials: list[DailySpecial]

    # Crew subscriptions
    crews_subscribed: int
    boxes_pre_ordered: int

    notes: Optional[str] = None


# ================================================================
# THOMMY'S DASHBOARD — The Crew Leader View
# ================================================================

class CrewLeaderDashboard(BaseModel):
    """What Thommy sees"""
    crew_leader: str
    crew_name: Optional[str]
    crew_size: int

    # This week
    orders_this_week: int
    total_spent_chf: Decimal
    total_saved_vs_gas_station: Decimal

    # Nutrition tracking
    avg_calories_per_worker: int
    avg_nutrient_grade: str

    # Favorites
    most_ordered_box: str
    most_ordered_coffee: str

    # Next order
    next_pickup_time: Optional[datetime]
    next_pickup_location: Optional[str]

    # The message
    thommy_says: str  # "Oh what a beautiful day!"


# ================================================================
# PRE-BUILT BOXES — The Cookie Cutters
# ================================================================

THOMMY_CONSTRUCTION_BOX = {
    "name": "Thommy's Drywall Special",
    "description": "5 sheets of drywall? You need this.",
    "worker_type": "construction",
    "energy_level": "extreme",
    "meal_type": "lunch",
    "items": [
        "Molly's Farm Sandwich (no tuna)",
        "Pink Punch 500ml",
        "2x Biberli",
        "Cheese wedge",
        "Apple (farm fresh)",
    ],
    "total_calories": 1200,
    "total_protein_g": 45,
    "nutrient_grade": "A",
    "price_chf": "12.50",
    "gas_station_equivalent_chf": "25.00",
    "savings_chf": "12.50",
}

MORNING_PINK_PUNCH_BOX = {
    "name": "Pink Punch Breakfast",
    "description": "Thommy's secret: Start the day RIGHT.",
    "worker_type": "construction",
    "energy_level": "heavy",
    "meal_type": "breakfast",
    "items": [
        "Pink Punch 500ml",
        "Farm eggs (2)",
        "Brown bread slice",
        "Butter pack",
        "Molly's jam",
    ],
    "total_calories": 650,
    "total_protein_g": 25,
    "nutrient_grade": "A",
    "price_chf": "8.00",
    "gas_station_equivalent_chf": "15.00",
    "savings_chf": "7.00",
}

COFFEE_BREAK_PACK = {
    "name": "10:30 Coffee Break",
    "description": "Better than Red Bull. Real energy.",
    "worker_type": "construction",
    "energy_level": "heavy",
    "meal_type": "morning_snack",
    "items": [
        "100 Calorie Coffee",
        "2x Biberli",
        "Water 500ml",
    ],
    "total_calories": 350,
    "total_protein_g": 8,
    "nutrient_grade": "B",
    "price_chf": "5.50",
    "gas_station_equivalent_chf": "12.00",
    "savings_chf": "6.50",
}

DONNY_BOY_SPECIAL = {
    "name": "Donny's Got You Covered",
    "description": "For the boys who work past 10:30.",
    "worker_type": "construction",
    "energy_level": "extreme",
    "meal_type": "lunch",
    "items": [
        "Double sandwich (no tuna)",
        "100 Calorie Coffee x2",
        "Water with gas 500ml",
        "Energy bar",
        "Fruit pack",
    ],
    "total_calories": 1500,
    "total_protein_g": 55,
    "nutrient_grade": "A",
    "price_chf": "15.00",
    "gas_station_equivalent_chf": "32.00",
    "savings_chf": "17.00",
}

MOLLY_SALAD_BOX = {
    "name": "Molly's Mountain Salad",
    "description": "100 Island baked in. Goat milk dressing. The secret.",
    "worker_type": "farm",
    "energy_level": "heavy",
    "meal_type": "lunch",
    "items": [
        "Mountain salad (large)",
        "Goat milk dressing",
        "Brown bread (2 slices)",
        "Cheese (farm fresh)",
        "Pink Punch 500ml",
    ],
    "total_calories": 900,
    "total_protein_g": 35,
    "nutrient_grade": "A+",
    "price_chf": "14.00",
    "gas_station_equivalent_chf": "28.00",
    "savings_chf": "14.00",
}


# ================================================================
# THE BOTTOM LINE
# ================================================================

HIGHWAY_ROBBERY_EXPOSED = """
┌─────────────────────────────────────────────────────────────┐
│                  HIGHWAY ROBBERY EXPOSED                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GAS STATION:                  MOLLY'S BOX:                │
│  ├─ 7 CHF sandwich             ├─ 12.50 CHF full box       │
│  ├─ ZERO nutrient              ├─ 1200 calories            │
│  ├─ Grade: F                   ├─ Grade: A                 │
│  ├─ Brown bread? NO            ├─ Farm fresh               │
│  ├─ Value? NONE                ├─ Real nutrition           │
│  └─ Taste? Meh                 └─ Thommy approved          │
│                                                             │
│  Total for crew of 5:          Total for crew of 5:        │
│  ├─ 5 x 15 CHF = 75 CHF        ├─ 5 x 12.50 = 62.50 CHF   │
│  ├─ Still hungry               ├─ Full and fueled          │
│  └─ Grade: F                   └─ Grade: A                 │
│                                                             │
│  SAVINGS: 12.50 CHF per day per worker                     │
│  WEEKLY (5 days): 62.50 CHF per worker                     │
│  CREW OF 5 WEEKLY: 312.50 CHF SAVED                        │
│                                                             │
│  "Oh what a beautiful day!" — Thommy                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
"""

THE_COOKIE_CUTTER = """
┌─────────────────────────────────────────────────────────────┐
│              THE COOKIE CUTTER — Same System                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MOLLY (Farm):        FELIX (Lab):        SAL (Bar):       │
│  ├─ Makes packages    ├─ Tests batches    ├─ Distributes   │
│  ├─ Farm fresh        ├─ Lab verified     ├─ Ready to grab │
│  ├─ Jugs              ├─ Teeny weeny      ├─ Quick orders  │
│  └─ The recipe        └─ The science      └─ The network   │
│                                                             │
│                    ↓ SAME SYSTEM ↓                         │
│                                                             │
│  THOMMY'S CREW:                                            │
│  ├─ Grab SANDs                                             │
│  ├─ Real nutrition                                         │
│  ├─ No highway robbery                                     │
│  ├─ "We got work to do"                                    │
│  └─ "Oh what a beautiful day!"                             │
│                                                             │
│  THE YAGNI DANCE:                                          │
│  ├─ Don't build what you don't need                        │
│  ├─ Same principle, different scale                        │
│  └─ Cookie cutter the formula                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
"""
