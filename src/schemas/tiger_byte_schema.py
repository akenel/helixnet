# File: src/schemas/tiger_byte_schema.py
"""
🐅 TIGER BYTE — WTQ Lunch Pack To Go
====================================

The Vision:
- 5 Francs. Take it or leave it.
- Hungry men on the job
- Hemp pressed spork (EAT THE UTENSIL)
- Fabio's cheese
- CBD Creme (my pants!)
- Vitamins ABCD
- Instant coffee (Arabica, Peruvian — just add water)
- Coffee Mate (makes everything taste great)

The Paul Principle:
- No seconds, no thirds (that's MEMBER stuff)
- But always a little stash for Paul (little brother)
- Not endless refill — that's happy hour, events
- Brother stuff = member band = loyalty

The Hemp Revolution:
- Hemp pressed spork (local made)
- Hemp wraps (eat the wrapper)
- Hemp tools (chopsticks, utensils)
- Chinese department for the chops
- NO PLASTIC. NO SWISS KNIFE (they got their own)

Nestlé folks = genius? NO.
HELIX logix = YAGNI = BUILD WHAT YOU NEED.

🐅🦁 Tiger Byte and Flow — So smooth wraps to go.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from enum import Enum
from decimal import Decimal


# ================================================================
# ENUMS
# ================================================================

class PackSizeEnum(str, Enum):
    """How hungry?"""
    BYTE = "byte"                # 5 CHF — the quick bite
    KILOBYTE = "kilobyte"        # 8 CHF — regular lunch
    MEGABYTE = "megabyte"        # 12 CHF — hungry tiger
    GIGABYTE = "gigabyte"        # 18 CHF — feed the crew


class UtensilTypeEnum(str, Enum):
    """Hemp tools — eat them after"""
    HEMP_SPORK = "hemp_spork"           # Fork + spoon, pressed hemp
    HEMP_CHOPSTICKS = "hemp_chopsticks"  # Chinese department
    HEMP_KNIFE = "hemp_knife"           # Spread the cheese
    HEMP_STRAW = "hemp_straw"           # For the Pink Punch
    EDIBLE_SPOON = "edible_spoon"       # Bread spoon


class WrapTypeEnum(str, Enum):
    """The carrier — no plastic"""
    HEMP_WRAP = "hemp_wrap"       # Eat the wrapper
    BREAD_BOWL = "bread_bowl"     # The container IS the food
    CHEESE_SHELL = "cheese_shell" # Fabio's crispy cheese
    LEAF_WRAP = "leaf_wrap"       # Lettuce, cabbage
    PAPER_CONE = "paper_cone"     # Compostable


class CoffeeTypeEnum(str, Enum):
    """Just add water"""
    ARABICA = "arabica"           # Smooth
    PERUVIAN = "peruvian"         # Bold
    INSTANT_MIX = "instant_mix"   # With Coffee Mate
    PINK_PUNCH = "pink_punch"     # Not coffee but YES


class MemberBandEnum(str, Enum):
    """The loyalty tiers"""
    GUEST = "guest"               # One time, full price
    REGULAR = "regular"           # 10% off
    BROTHER = "brother"           # Paul's tier — little extra stash
    TIGER = "tiger"               # Happy hour access
    FOUNDER = "founder"           # Events, unlimited extras


# ================================================================
# THE TIGER BYTE PACK — 5 Francs, Take It or Leave It
# ================================================================

class TigerByteBase(BaseModel):
    """The 5 Franc Miracle"""
    name: str = Field(..., max_length=100)
    pack_size: PackSizeEnum = PackSizeEnum.BYTE

    # What's inside
    bread_type: str = Field(default="Local fresh", max_length=50)
    cheese_type: str = Field(default="Fabio's farm cheese", max_length=50)
    protein: Optional[str] = Field(None, max_length=50)  # Optional meat/egg

    # The specials
    has_cbd_creme: bool = False
    cbd_creme_type: Optional[str] = None  # "Tony Boz Power Creme"

    # Vitamins ABCD
    vitamin_a: bool = True
    vitamin_b: bool = True
    vitamin_c: bool = True
    vitamin_d: bool = True

    # The utensil (eat it after!)
    utensil: UtensilTypeEnum = UtensilTypeEnum.HEMP_SPORK
    wrap: WrapTypeEnum = WrapTypeEnum.HEMP_WRAP

    # Coffee add-on
    has_coffee: bool = False
    coffee_type: Optional[CoffeeTypeEnum] = None
    has_coffee_mate: bool = False  # Makes everything taste great!

    # Nutrition
    calories: int = Field(default=450, ge=0)
    protein_g: float = Field(default=15, ge=0)

    # Price
    price_chf: Decimal = Field(default=Decimal("5.00"), ge=0)


class TigerByteCreate(TigerByteBase):
    pass


class TigerByteRead(TigerByteBase):
    id: UUID
    times_ordered: int = 0
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# HEMP UTENSILS — Local Made, Eat After
# ================================================================

class HempUtensilBase(BaseModel):
    """The tools you can eat"""
    name: str = Field(..., max_length=100)
    utensil_type: UtensilTypeEnum

    # Material
    material: str = Field(default="Pressed hemp fiber", max_length=100)
    is_edible: bool = True
    is_compostable: bool = True

    # Source
    made_locally: bool = True
    made_by: str = Field(default="Local hemp workshop", max_length=100)

    # Specs
    weight_g: float = Field(default=15, ge=0)
    strength_rating: str = Field(default="Soup-proof", max_length=50)

    # Price (bulk)
    price_per_100: Decimal = Field(default=Decimal("25.00"), ge=0)


class HempUtensilRead(HempUtensilBase):
    id: UUID
    in_stock: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# FABIO'S CHEESE — The Real Deal
# ================================================================

class FabioCheeseBase(BaseModel):
    """Fabio has cheese. The REAL cheese."""
    name: str = Field(..., max_length=100)
    cheese_type: str = Field(..., max_length=50)  # Hard, soft, cream

    # Source
    farm_name: str = Field(default="Fabio's Farm", max_length=100)
    milk_source: str = Field(default="Goat", max_length=50)  # Goat, cow, sheep

    # Taste
    aged_months: int = Field(default=3, ge=0)
    flavor_profile: str = Field(default="Sharp, creamy", max_length=100)

    # Nutrition per 30g
    calories: int = Field(default=110, ge=0)
    protein_g: float = Field(default=7, ge=0)
    fat_g: float = Field(default=9, ge=0)

    # CBD option
    has_cbd_infusion: bool = False
    cbd_mg_per_serving: int = Field(default=0, ge=0)

    price_per_kg: Decimal = Field(default=Decimal("28.00"), ge=0)


class FabioCheeseRead(FabioCheeseBase):
    id: UUID
    in_stock_kg: float = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# CBD CREME — My Pants! (Tony Boz Special)
# ================================================================

class CBDCremeBase(BaseModel):
    """The CBD Creme that makes your pants happy"""
    name: str = Field(..., max_length=100)
    creme_type: str = Field(default="Spreadable", max_length=50)

    # CBD content
    cbd_mg_per_serving: int = Field(default=25, ge=0)
    thc_free: bool = True

    # Base
    base_ingredient: str = Field(default="Goat milk cream", max_length=100)
    flavor: str = Field(default="Herb blend", max_length=50)

    # Usage
    serving_size_g: int = Field(default=15, ge=1)
    servings_per_jar: int = Field(default=20, ge=1)

    # Tested
    lab_tested: bool = True
    tested_by: str = Field(default="Felix Lab", max_length=100)

    price_per_jar: Decimal = Field(default=Decimal("18.00"), ge=0)


class CBDCremeRead(CBDCremeBase):
    id: UUID
    in_stock: int = 0
    batch_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# INSTANT COFFEE PACK — Just Add Water
# ================================================================

class InstantCoffeeBase(BaseModel):
    """Arabica, Peruvian — just add water"""
    name: str = Field(..., max_length=100)
    coffee_type: CoffeeTypeEnum

    # Origin
    origin: str = Field(default="Peru", max_length=50)
    roast_level: str = Field(default="Medium", max_length=20)

    # Pack
    pack_size_g: int = Field(default=3, ge=1)  # Single serving
    servings_per_box: int = Field(default=10, ge=1)

    # Add-ons included
    includes_coffee_mate: bool = True  # Makes everything taste great!
    includes_sugar: bool = False

    # Caffeine
    caffeine_mg: int = Field(default=95, ge=0)

    price_per_box: Decimal = Field(default=Decimal("8.00"), ge=0)
    price_per_single: Decimal = Field(default=Decimal("1.00"), ge=0)


class InstantCoffeeRead(InstantCoffeeBase):
    id: UUID
    in_stock_boxes: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE PAUL PRINCIPLE — Little Brother Stash
# ================================================================

class PaulPrincipleConfig(BaseModel):
    """
    No seconds, no thirds — that's MEMBER stuff.
    But always a little stash for Paul.
    Brother stuff.
    """
    # The rule
    max_refills_guest: int = 0      # None for guests
    max_refills_regular: int = 1    # One extra
    max_refills_brother: int = 2    # Paul's tier — little stash
    max_refills_tiger: int = 3      # Happy hour
    max_refills_founder: int = 5    # Events, but still not endless

    # The stash
    stash_location: str = "Hidden in the pan"
    stash_for: str = "Paul (little brother)"

    # The events
    happy_hour_enabled: bool = True
    happy_hour_start: str = "16:00"
    happy_hour_end: str = "18:00"

    # Extra cookie with salad (members only)
    extra_cookie_for_members: bool = True
    extra_coffee_for_members: bool = True

    # The truth
    endless_refill: bool = False  # NEVER. This is brother stuff.


# ================================================================
# MEMBER BAND — The Loyalty System
# ================================================================

class MemberBandBase(BaseModel):
    """The band of brothers (and tigers)"""
    name: str = Field(..., max_length=100)
    band_tier: MemberBandEnum = MemberBandEnum.REGULAR

    # Benefits
    discount_percent: int = Field(default=0, ge=0, le=50)
    free_coffee_per_week: int = Field(default=0, ge=0)
    free_cookie_with_salad: bool = False
    happy_hour_access: bool = False
    event_access: bool = False

    # The Paul stash
    extra_stash_allowed: bool = False
    stash_items: list[str] = []

    # Points
    points_per_chf: int = Field(default=1, ge=0)
    points_balance: int = Field(default=0, ge=0)


class MemberBandRead(MemberBandBase):
    id: UUID
    member_since: datetime
    total_orders: int = 0
    total_spent_chf: Decimal = Decimal("0")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# THE TIGER BYTE MENU — Pre-Built Packs
# ================================================================

TIGER_BYTE_MENU = {
    "byte_basic": {
        "name": "Tiger Byte Basic",
        "pack_size": "byte",
        "description": "5 Francs. Bread + Fabio's Cheese. Done.",
        "contents": [
            "Fresh bread roll",
            "Fabio's cheese (30g)",
            "Hemp spork (eat it!)",
        ],
        "price_chf": "5.00",
        "calories": 350,
        "vitamins": ["A", "B"],
    },
    "byte_cbd": {
        "name": "Tiger Byte CBD",
        "pack_size": "byte",
        "description": "5 Francs + CBD Creme. Your pants will thank you.",
        "contents": [
            "Fresh bread roll",
            "Fabio's cheese (30g)",
            "CBD Creme (15g)",
            "Hemp spork",
        ],
        "price_chf": "7.00",
        "calories": 420,
        "vitamins": ["A", "B", "D"],
        "cbd_mg": 25,
    },
    "kilobyte_lunch": {
        "name": "Tiger Kilobyte",
        "pack_size": "kilobyte",
        "description": "Full lunch. Bread, cheese, salad, coffee.",
        "contents": [
            "Fresh bread (2 rolls)",
            "Fabio's cheese (50g)",
            "Side salad (Molly's)",
            "Instant coffee pack (Arabica)",
            "Coffee Mate sachet",
            "Hemp spork + knife",
        ],
        "price_chf": "8.00",
        "calories": 650,
        "vitamins": ["A", "B", "C", "D"],
    },
    "megabyte_feast": {
        "name": "Tiger Megabyte",
        "pack_size": "megabyte",
        "description": "Hungry tiger meal. Everything.",
        "contents": [
            "Fresh bread (2 rolls)",
            "Fabio's cheese (80g)",
            "Full salad (Molly's special)",
            "CBD Creme portion",
            "Protein (egg or meat)",
            "Instant coffee + Coffee Mate",
            "Pink Punch 250ml",
            "Hemp utensil set",
            "Extra cookie (members)",
        ],
        "price_chf": "12.00",
        "calories": 950,
        "vitamins": ["A", "B", "C", "D"],
        "cbd_mg": 25,
    },
    "gigabyte_crew": {
        "name": "Tiger Gigabyte (Crew Pack)",
        "pack_size": "gigabyte",
        "description": "Feed 4 hungry workers. Thommy's order.",
        "contents": [
            "4x Tiger Kilobyte packs",
            "Extra bread basket",
            "Fabio's cheese wheel (200g)",
            "4x Instant coffee + Coffee Mate",
            "Pink Punch 1L",
            "4x Hemp utensil sets",
        ],
        "price_chf": "35.00",
        "price_per_person": "8.75",
        "calories_per_person": 750,
        "crew_size": 4,
    },
}


# ================================================================
# HAPPY HOUR & EVENTS — Member Band Specials
# ================================================================

HAPPY_HOUR_RULES = {
    "name": "Tiger Happy Hour",
    "hours": "16:00 - 18:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "benefits": {
        "guest": "Nothing (become a member!)",
        "regular": "Free coffee refill",
        "brother": "Free coffee + cookie",
        "tiger": "Free coffee + cookie + 20% off food",
        "founder": "Free coffee + cookie + 30% off + event access",
    },
    "the_rule": "No seconds, no thirds for guests. Brother stash for members.",
}

EVENT_SPECIALS = {
    "saturday_market": {
        "name": "Saturday Market Special",
        "description": "Overstock clearance. Deep discounts.",
        "discount_percent": 40,
        "member_only": False,
    },
    "founder_night": {
        "name": "Founder Night",
        "description": "Monthly meetup. Free food. Stories.",
        "discount_percent": 100,
        "member_only": True,
        "tier_required": "founder",
    },
    "paul_day": {
        "name": "Paul's Day (Little Brother Special)",
        "description": "Extra stash for everyone. In memory of the little brothers.",
        "extra_cookie": True,
        "extra_coffee": True,
        "member_only": False,
    },
}


# ================================================================
# THE MANIFESTO
# ================================================================

TIGER_BYTE_MANIFESTO = """
┌─────────────────────────────────────────────────────────────────────┐
│                    TIGER BYTE — The Manifesto                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  5 FRANCS. TAKE IT OR LEAVE IT.                                    │
│                                                                     │
│  WHAT'S INSIDE:                                                     │
│  ├─ Bread (local, fresh)                                           │
│  ├─ Fabio's Cheese (the real deal)                                 │
│  ├─ CBD Creme (optional — my pants!)                               │
│  ├─ Vitamins ABCD (you need fuel)                                  │
│  ├─ Hemp spork (eat it after)                                      │
│  └─ Coffee pack (Arabica + Coffee Mate)                            │
│                                                                     │
│  THE PAUL PRINCIPLE:                                                │
│  ├─ No seconds, no thirds (for guests)                             │
│  ├─ Little stash for Paul (brother tier)                           │
│  ├─ Happy hour for Tigers                                          │
│  ├─ Events for Founders                                            │
│  └─ NOT endless refill — this is BROTHER stuff                     │
│                                                                     │
│  THE HEMP REVOLUTION:                                               │
│  ├─ Hemp spork (pressed, local made)                               │
│  ├─ Hemp chopsticks (Chinese department)                           │
│  ├─ Hemp wrap (eat the wrapper)                                    │
│  ├─ Hemp straw (for Pink Punch)                                    │
│  └─ NO PLASTIC. NO SWISS KNIFE (you got your own)                  │
│                                                                     │
│  COFFEE MATE: Makes everything taste great.                        │
│                                                                     │
│  Nestlé folks = genius? NO.                                        │
│  HELIX logix = YAGNI = Build what you need.                        │
│                                                                     │
│  WE ARE PACKING LUNCH BYTES TO GO.                                 │
│                                                                     │
│  🐅 TIGER BYTE AND FLOW — So smooth wraps to go.                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

THE_COFFEE_MATE_TRUTH = """
┌─────────────────────────────────────────────────────────────────────┐
│              COFFEE MATE — What Makes Everything Taste Great        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INSTANT COFFEE PACK:                                              │
│  ├─ Arabica (smooth, 95mg caffeine)                                │
│  ├─ Peruvian (bold, mountain grown)                                │
│  ├─ Just add water                                                 │
│  └─ Coffee Mate sachet included                                    │
│                                                                     │
│  WHY IT WORKS:                                                      │
│  ├─ No machine needed                                              │
│  ├─ Job site ready                                                 │
│  ├─ Hot water from thermos                                         │
│  └─ Better than gas station garbage                                │
│                                                                     │
│  1 CHF per cup. Gas station: 4.50 CHF.                            │
│  YOU SAVE: 3.50 CHF per coffee.                                    │
│  WEEKLY (10 coffees): 35 CHF saved.                                │
│                                                                     │
│  "What makes everything taste great?"                              │
│  COFFEE MATE + TIGER BYTE + BE WATER.                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""
