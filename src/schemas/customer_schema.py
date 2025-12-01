# File: src/schemas/customer_schema.py
"""
Customer & CRACK Profile Schemas

The heart of HelixNETWORK loyalty - where CRACKs earn credits
for purchases AND knowledge contributions.

"Knowledge is the gold" - KB-032
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional, List
from enum import Enum


# ================================================================
# ENUMS
# ================================================================

class CrackLevel(str, Enum):
    """CRACK progression levels - from zero to hero"""
    SEEDLING = "seedling"      # Just joined, learning
    SPROUT = "sprout"          # First KB written
    ROOTED = "rooted"          # 5+ KBs, regular contributor
    GROWING = "growing"        # 10+ KBs, mentoring others
    BLAZING = "blazing"        # 25+ KBs, community leader
    ORACLE = "oracle"          # The masters (Mosey, Felix level)


class LoyaltyTier(str, Enum):
    """Spending-based tiers - auto-calculated"""
    BRONZE = "bronze"          # 0-199 CHF → 5% off
    SILVER = "silver"          # 200-499 CHF → 10% off
    GOLD = "gold"              # 500-999 CHF → 15% off
    PLATINUM = "platinum"      # 1000+ CHF → 20% off
    DIAMOND = "diamond"        # 2500+ CHF → 25% + VIP


class PreferredContact(str, Enum):
    """How does this CRACK want to be reached?"""
    EMAIL = "email"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    NONE = "none"              # Privacy first


class KBStatus(str, Enum):
    """KB approval workflow status"""
    DRAFT = "draft"            # CRACK is writing
    SUBMITTED = "submitted"    # Ready for review
    IN_REVIEW = "in_review"    # CRACKs reviewing
    APPROVED = "approved"      # Owner approved
    PUBLISHED = "published"    # Live in system
    REJECTED = "rejected"      # Needs revision


# ================================================================
# CREDIT SYSTEM CONSTANTS
# ================================================================

# Purchase credits
CREDITS_PER_CHF = 1                    # 1 CHF = 1 credit

# Action credits
CREDITS_FIRST_PURCHASE = 20
CREDITS_ADD_INSTAGRAM = 10
CREDITS_ADD_TELEGRAM = 10
CREDITS_ADD_EMAIL = 5
CREDITS_REFERRAL = 100                 # For referrer
CREDITS_REFERRED = 50                  # For new customer
CREDITS_BIRTHDAY_MULTIPLIER = 2        # 2x during birthday week
CREDITS_PERFECT_CHECKOUT = 5           # No returns, clean transaction
CREDITS_WEEKLY_STREAK = 25             # Visit 3x in a week

# KB credits - KNOWLEDGE IS GOLD
CREDITS_KB_DRAFT = 0                   # Nothing until submitted
CREDITS_KB_SUBMITTED = 10              # Thanks for trying
CREDITS_KB_APPROVED = 100              # Base approval credit
CREDITS_KB_PUBLISHED = 50              # Bonus when live
CREDITS_KB_REVIEW = 25                 # For reviewing others' KBs
CREDITS_KB_FEATURED = 250              # Featured KB of the week

# KB quality bonuses
CREDITS_KB_WITH_IMAGES = 25
CREDITS_KB_WITH_VIDEO = 50
CREDITS_KB_WITH_BOM = 75               # Bill of Materials (recipe)
CREDITS_KB_WITH_LAB_REPORT = 100       # Lab tested

# Redemption
CREDITS_FOR_VOUCHER_5 = 100            # 100 credits = CHF 5
CREDITS_FOR_VOUCHER_10 = 180           # 180 credits = CHF 10 (bonus)
CREDITS_FOR_VOUCHER_25 = 400           # 400 credits = CHF 25 (big bonus)

# Tier thresholds (lifetime spend)
TIER_BRONZE_MIN = Decimal("0")
TIER_SILVER_MIN = Decimal("200")
TIER_GOLD_MIN = Decimal("500")
TIER_PLATINUM_MIN = Decimal("1000")
TIER_DIAMOND_MIN = Decimal("2500")

# Tier discounts
TIER_DISCOUNTS = {
    LoyaltyTier.BRONZE: Decimal("5"),
    LoyaltyTier.SILVER: Decimal("10"),
    LoyaltyTier.GOLD: Decimal("15"),
    LoyaltyTier.PLATINUM: Decimal("20"),
    LoyaltyTier.DIAMOND: Decimal("25"),
}


# ================================================================
# CUSTOMER PROFILE SCHEMAS
# ================================================================

class CustomerBase(BaseModel):
    """Base customer/CRACK profile"""

    # Identity
    handle: str = Field(..., max_length=50, description="Public handle (Poppie)")
    real_name: Optional[str] = Field(None, max_length=100, description="Private (Larry)")

    # Contact
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

    # Social - The CRACK channels
    instagram: Optional[str] = Field(None, max_length=100, description="@poppie_420")
    telegram: Optional[str] = Field(None, max_length=100, description="@poppie")
    whatsapp: Optional[str] = Field(None, max_length=50)

    preferred_contact: PreferredContact = Field(
        default=PreferredContact.INSTAGRAM,
        description="How to reach this CRACK"
    )

    # Personal
    birthday: Optional[date] = Field(None, description="For birthday bonuses")
    language: str = Field(default="de", max_length=5, description="de/en/fr/it")

    # Staff notes
    notes: Optional[str] = Field(None, max_length=1000, description="Internal notes")


class CustomerCreate(CustomerBase):
    """Create a new CRACK profile"""
    referrer_id: Optional[UUID] = Field(None, description="Who referred them")


class CustomerUpdate(BaseModel):
    """Update CRACK profile (all optional)"""
    handle: Optional[str] = Field(None, max_length=50)
    real_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    instagram: Optional[str] = Field(None, max_length=100)
    telegram: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=50)
    preferred_contact: Optional[PreferredContact] = None
    birthday: Optional[date] = None
    language: Optional[str] = Field(None, max_length=5)
    notes: Optional[str] = Field(None, max_length=1000)


class CustomerRead(CustomerBase):
    """Full customer profile with loyalty data"""
    id: UUID

    # Loyalty - Spending tier
    loyalty_tier: LoyaltyTier = Field(default=LoyaltyTier.BRONZE)
    lifetime_spend: Decimal = Field(default=Decimal("0"))
    tier_discount_percent: Decimal = Field(default=Decimal("5"))

    # Credits - Gamification
    credits_balance: int = Field(default=0, description="Current spendable credits")
    credits_earned_total: int = Field(default=0, description="All-time earned")
    credits_spent_total: int = Field(default=0, description="All-time redeemed")

    # CRACK Level - Knowledge contribution
    crack_level: CrackLevel = Field(default=CrackLevel.SEEDLING)
    crack_group: Optional[int] = Field(None, description="Group 7, etc.")
    crack_team: Optional[str] = Field(None, max_length=100, description="Pink Punch Squad")

    # KB Contributions
    kbs_written: int = Field(default=0)
    kbs_approved: int = Field(default=0)
    kbs_featured: int = Field(default=0)
    kb_credits_earned: int = Field(default=0)

    # Activity
    first_purchase: Optional[datetime] = None
    last_purchase: Optional[datetime] = None
    last_visit: Optional[datetime] = None
    visit_count: int = Field(default=0)
    purchase_count: int = Field(default=0)
    average_basket: Decimal = Field(default=Decimal("0"))

    # Favorites
    favorite_products: List[str] = Field(default_factory=list)
    favorite_categories: List[str] = Field(default_factory=list)

    # Referrals
    referrer_id: Optional[UUID] = None
    referrals_made: int = Field(default=0)
    referral_credits_earned: int = Field(default=0)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# KB CONTRIBUTION SCHEMAS
# ================================================================

class KBContributionBase(BaseModel):
    """A CRACK's KB contribution"""
    title: str = Field(..., max_length=255)
    summary: str = Field(..., max_length=500, description="What this KB teaches")
    category: str = Field(..., max_length=100, description="recipe/protocol/guide/etc")

    # Content flags (affect credits)
    has_images: bool = Field(default=False)
    has_video: bool = Field(default=False)
    has_bom: bool = Field(default=False, description="Bill of Materials / Recipe")
    has_lab_report: bool = Field(default=False)

    # JH Reference
    jh_reference: Optional[str] = Field(None, max_length=100, description="JH-Chapter-8")


class KBContributionCreate(KBContributionBase):
    """Submit a new KB"""
    content_path: str = Field(..., description="Path to KB markdown file")


class KBContributionRead(KBContributionBase):
    """KB with full metadata"""
    id: UUID
    author_id: UUID
    author_handle: str

    # Workflow
    status: KBStatus = Field(default=KBStatus.DRAFT)
    submitted_at: Optional[datetime] = None
    reviewed_by: List[UUID] = Field(default_factory=list)
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    # Credits
    base_credits: int = Field(default=0)
    bonus_credits: int = Field(default=0)
    total_credits: int = Field(default=0)

    # Stats
    view_count: int = Field(default=0)
    rating_average: Decimal = Field(default=Decimal("0"))
    rating_count: int = Field(default=0)
    is_featured: bool = Field(default=False)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KBReview(BaseModel):
    """CRACK reviews another CRACK's KB"""
    kb_id: UUID
    reviewer_id: UUID
    rating: int = Field(..., ge=1, le=5, description="1-5 stars")
    comment: Optional[str] = Field(None, max_length=500)
    recommend_approval: bool = Field(default=False)


class KBApproval(BaseModel):
    """Owner batch approval"""
    kb_ids: List[UUID] = Field(..., description="KBs to approve")
    approve_all: bool = Field(default=False, description="Select all shortcut")
    notes: Optional[str] = Field(None, max_length=500)


# ================================================================
# CREDIT TRANSACTION SCHEMAS
# ================================================================

class CreditTransactionType(str, Enum):
    """How credits were earned/spent"""
    PURCHASE = "purchase"
    REFERRAL = "referral"
    KB_SUBMITTED = "kb_submitted"
    KB_APPROVED = "kb_approved"
    KB_PUBLISHED = "kb_published"
    KB_FEATURED = "kb_featured"
    KB_REVIEW = "kb_review"
    ACTION_BONUS = "action_bonus"
    BIRTHDAY_BONUS = "birthday_bonus"
    STREAK_BONUS = "streak_bonus"
    REDEMPTION = "redemption"
    ADJUSTMENT = "adjustment"         # Manual adjustment by owner
    EVENT_PRIZE = "event_prize"       # HelixCup 2026, etc.


class CreditTransaction(BaseModel):
    """Record of credit earning/spending"""
    id: UUID
    customer_id: UUID

    transaction_type: CreditTransactionType
    credits: int = Field(..., description="Positive = earned, negative = spent")
    balance_after: int

    # Context
    reference_id: Optional[UUID] = Field(None, description="Related KB, order, etc.")
    reference_type: Optional[str] = Field(None, description="kb/order/event")
    description: str = Field(..., max_length=255)

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# COUPON SCHEMAS
# ================================================================

class CouponType(str, Enum):
    """What kind of discount"""
    PERCENT = "percent"            # 10% off
    FIXED = "fixed"                # CHF 5 off
    FREE_PRODUCT = "free_product"  # Free item
    FREE_SHIPPING = "free_shipping"


class CouponBase(BaseModel):
    """Discount coupon"""
    code: str = Field(..., max_length=50, description="WELCOME10")
    description: str = Field(..., max_length=255)

    coupon_type: CouponType
    value: Decimal = Field(..., description="10 for 10%, or 5 for CHF 5")

    # Restrictions
    min_purchase: Decimal = Field(default=Decimal("0"))
    max_discount: Optional[Decimal] = Field(None, description="Cap for % coupons")
    max_uses_total: Optional[int] = Field(None)
    max_uses_per_customer: int = Field(default=1)

    # Targeting
    tier_required: Optional[LoyaltyTier] = None
    crack_level_required: Optional[CrackLevel] = None
    first_purchase_only: bool = Field(default=False)

    # Validity
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool = Field(default=True)


class CouponCreate(CouponBase):
    """Create a new coupon"""
    pass


class CouponRead(CouponBase):
    """Coupon with usage stats"""
    id: UUID
    uses_count: int = Field(default=0)
    total_discount_given: Decimal = Field(default=Decimal("0"))
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# EVENT / PRIZE SCHEMAS
# ================================================================

class EventPrize(BaseModel):
    """HelixCup 2026, Beach Party, etc."""
    id: UUID
    event_name: str = Field(..., max_length=255, description="HelixCup 2026")
    prize_name: str = Field(..., max_length=255, description="Platinum CRACK Award")

    # What they win
    credits_prize: int = Field(default=0)
    voucher_value: Decimal = Field(default=Decimal("0"))
    physical_prize: Optional[str] = Field(None, description="Travel package, etc.")

    # Requirements
    min_crack_level: Optional[CrackLevel] = None
    min_kbs_written: int = Field(default=0)
    min_tier: Optional[LoyaltyTier] = None

    # Winner
    winner_id: Optional[UUID] = None
    awarded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# QUICK LOOKUP AT CHECKOUT
# ================================================================

class CustomerCheckoutView(BaseModel):
    """
    What the cashier sees at checkout.
    Quick reference for personalized service.
    """
    # Identity
    handle: str
    instagram: Optional[str]

    # Tier & Discount
    loyalty_tier: LoyaltyTier
    tier_discount_percent: Decimal

    # Credits
    credits_balance: int
    credits_to_next_voucher: int

    # CRACK Status
    crack_level: CrackLevel
    kbs_written: int

    # Recent activity
    last_visit_days_ago: int
    favorite_products: List[str]

    # Alerts
    birthday_soon: bool = Field(default=False, description="Within 14 days")
    tier_upgrade_close: bool = Field(default=False, description="Within CHF 50")
    has_available_coupons: bool = Field(default=False)

    # Upsell suggestions
    suggested_products: List[str] = Field(default_factory=list)
    suggested_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def calculate_tier(lifetime_spend: Decimal) -> LoyaltyTier:
    """Determine tier based on lifetime spend"""
    if lifetime_spend >= TIER_DIAMOND_MIN:
        return LoyaltyTier.DIAMOND
    elif lifetime_spend >= TIER_PLATINUM_MIN:
        return LoyaltyTier.PLATINUM
    elif lifetime_spend >= TIER_GOLD_MIN:
        return LoyaltyTier.GOLD
    elif lifetime_spend >= TIER_SILVER_MIN:
        return LoyaltyTier.SILVER
    return LoyaltyTier.BRONZE


def calculate_kb_credits(kb: KBContributionBase, is_featured: bool = False) -> int:
    """Calculate total credits for a KB contribution"""
    credits = CREDITS_KB_APPROVED  # Base

    # Quality bonuses
    if kb.has_images:
        credits += CREDITS_KB_WITH_IMAGES
    if kb.has_video:
        credits += CREDITS_KB_WITH_VIDEO
    if kb.has_bom:
        credits += CREDITS_KB_WITH_BOM
    if kb.has_lab_report:
        credits += CREDITS_KB_WITH_LAB_REPORT

    # Featured bonus
    if is_featured:
        credits += CREDITS_KB_FEATURED

    return credits


def calculate_crack_level(kbs_approved: int) -> CrackLevel:
    """Determine CRACK level based on KB contributions"""
    if kbs_approved >= 25:
        return CrackLevel.BLAZING
    elif kbs_approved >= 10:
        return CrackLevel.GROWING
    elif kbs_approved >= 5:
        return CrackLevel.ROOTED
    elif kbs_approved >= 1:
        return CrackLevel.SPROUT
    return CrackLevel.SEEDLING
