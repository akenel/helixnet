# File: src/db/models/promo_model.py
"""
HelixPROMO - Every Penny for Mr. TAXMAN
"BLW and PAM proofed all the pennies" - Angel, Day One

In these shops there are free lights.
Free coffees. Free sandwiches. Free vibes.
But the AUDITOR wants receipts.

Track EVERYTHING you give away.
Because what's free for the customer
is a DEDUCTION for you.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum, Numeric, Boolean, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from .base import Base


# ================================================================
# ENUMS - The Ways Things Go Free
# ================================================================

class DiscountType(enum.Enum):
    """Types of discounts - Mr. TAXMAN needs categories"""
    # Comps - 100% free
    COMP_OWNER = "comp_owner"           # Owner's friends, landlord, partners
    COMP_VIP = "comp_vip"               # VIP customers, influencers
    COMP_STAFF = "comp_staff"           # Staff meals, staff drinks
    COMP_DAMAGE = "comp_damage"         # Made wrong, customer complaint fix

    # Promos - Marketing spend
    PROMO_NEW_CUSTOMER = "promo_new"    # First visit free coffee
    PROMO_LOYALTY = "promo_loyalty"     # Buy 10 get 1 free
    PROMO_EVENT = "promo_event"         # Grand opening, special day
    PROMO_INFLUENCER = "promo_influencer"  # Social media people

    # Samples - Product testing
    SAMPLE_PRODUCT = "sample_product"   # New product tasting
    SAMPLE_CBD = "sample_cbd"           # CBD samples (regulated)

    # Waste - Lost value
    WASTE_EXPIRED = "waste_expired"     # Past date
    WASTE_DAMAGED = "waste_damaged"     # Dropped, broken
    WASTE_THEFT = "waste_theft"         # Walked out without paying
    WASTE_MICHEL = "waste_michel"       # Michel used whole bottle

    # Member discounts - Partial
    MEMBER_REGULAR = "member_regular"   # 5% off
    MEMBER_JACK = "member_jack"         # 10% off
    MEMBER_VIP = "member_vip"           # 15% off
    MEMBER_FOUNDER = "member_founder"   # 20% off

    # Operational
    HOUSE_ACCOUNT = "house_account"     # Pay later arrangement
    BARTER = "barter"                   # Trade for services
    ROUND_DOWN = "round_down"           # Keep the change


class PromoStatus(enum.Enum):
    """Status of promo/discount"""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TaxCategory(enum.Enum):
    """Tax treatment categories - What Mr. TAXMAN sees"""
    PROMOTIONAL_EXPENSE = "promo_expense"       # Marketing deduction
    COST_OF_GOODS = "cogs"                      # Inventory loss
    STAFF_BENEFIT = "staff_benefit"             # May have tax implications
    ENTERTAINMENT = "entertainment"              # Client entertainment
    CHARITABLE = "charitable"                    # If registered charity
    NOT_DEDUCTIBLE = "not_deductible"           # Personal use, no deduction


# ================================================================
# DISCOUNT REASON MODEL - Why things are free
# ================================================================

class DiscountReasonModel(Base):
    """
    Preset discount reasons.

    Quick select for Andy at the register.
    "Boris lunch" → COMP_OWNER → ENTERTAINMENT
    """
    __tablename__ = 'discount_reasons'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Identity
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Quick name: 'Landlord Lunch', 'Staff Coffee'"
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        comment="Short code: LANDLORD, STAFF, VIP"
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Classification
    discount_type: Mapped[DiscountType] = mapped_column(
        SQLEnum(DiscountType),
        nullable=False
    )
    tax_category: Mapped[TaxCategory] = mapped_column(
        SQLEnum(TaxCategory),
        default=TaxCategory.PROMOTIONAL_EXPENSE
    )

    # Default discount
    default_percentage: Mapped[int] = mapped_column(
        Integer,
        default=100,
        comment="Default discount %: 100 = free, 10 = 10% off"
    )

    # Limits
    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Needs manager approval?"
    )
    max_daily_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Limit per day, null = unlimited"
    )
    max_value_chf: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Max single discount value"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<DiscountReasonModel(code='{self.code}', type='{self.discount_type.value}')>"


# ================================================================
# PROMO TRANSACTION MODEL - Every freebie tracked
# ================================================================

class PromoTransactionModel(Base):
    """
    Every single discount/comp/freebie.

    Boris's free Cappo? Tracked.
    Michel's wasted bottle? Tracked.
    Staff lunch? Tracked.

    Mr. TAXMAN sees ALL.
    """
    __tablename__ = 'promo_transactions'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # When
    transaction_date: Mapped[date] = mapped_column(
        Date,
        default=lambda: date.today(),
        index=True
    )
    transaction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # What was discounted
    item_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="What was given: '2x PAM Cappo, 1x Baloney Sandwich'"
    )

    # Values - THE PENNIES
    original_value: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Full retail value before discount"
    )
    discount_percentage: Mapped[int] = mapped_column(
        Integer,
        default=100,
        comment="Discount applied: 100 = free"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="CHF value of the discount"
    )
    final_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        comment="What customer actually paid"
    )

    # Why - Classification
    discount_type: Mapped[DiscountType] = mapped_column(
        SQLEnum(DiscountType),
        nullable=False,
        index=True
    )
    tax_category: Mapped[TaxCategory] = mapped_column(
        SQLEnum(TaxCategory),
        default=TaxCategory.PROMOTIONAL_EXPENSE,
        index=True
    )
    reason_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('discount_reasons.id', ondelete='SET NULL'),
        nullable=True
    )
    reason_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Custom note: 'Landlord meeting Day 1'"
    )

    # Who received it
    recipient_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Boris, Marco, Staff, Walk-in"
    )
    recipient_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="landlord, vendor, staff, customer, influencer"
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Link to member if applicable"
    )

    # Who gave it
    authorized_by: Mapped[str] = mapped_column(
        String(100),
        default="Andy",
        comment="Who approved this discount"
    )

    # Link to order if applicable
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Link to cafe_order or sale"
    )

    # Status
    status: Mapped[PromoStatus] = mapped_column(
        SQLEnum(PromoStatus),
        default=PromoStatus.USED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<PromoTransactionModel(date='{self.transaction_date}', value={self.discount_amount}, type='{self.discount_type.value}')>"


# ================================================================
# DAILY PROMO SUMMARY - Quick totals
# ================================================================

class DailyPromoSummaryModel(Base):
    """
    Daily rollup of all promos/comps.

    Andy checks this at end of day.
    "How much did I give away today?"
    """
    __tablename__ = 'daily_promo_summaries'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Date
    summary_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True
    )

    # Totals by type
    comp_owner_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    comp_vip_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    comp_staff_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    promo_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    sample_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    waste_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    member_discount_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    # Grand totals
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    total_discount_value: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        comment="Total CHF given away"
    )
    total_deductible: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        comment="Total that's tax deductible"
    )

    # Comparison
    revenue_today: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="For ratio calculation"
    )
    discount_to_revenue_ratio: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Percentage of revenue given as discount"
    )

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
        return f"<DailyPromoSummaryModel(date='{self.summary_date}', total={self.total_discount_value})>"


# ================================================================
# TAX REPORT MODEL - Mr. TAXMAN's favorite
# ================================================================

class TaxReportModel(Base):
    """
    Monthly/Yearly tax reports.

    This is what the AUDITOR wants.
    Categorized. Totaled. Ready for filing.
    """
    __tablename__ = 'tax_reports'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Period
    report_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="monthly, quarterly, yearly"
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Totals by tax category
    promotional_expense: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Marketing/promo - deductible"
    )
    cost_of_goods: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Waste/damage - deductible"
    )
    staff_benefits: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Staff meals - partially deductible"
    )
    entertainment: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Client entertainment - partially deductible"
    )
    charitable: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Donations - deductible if registered"
    )
    not_deductible: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="Personal use - NOT deductible"
    )

    # Grand totals
    total_discounts: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_deductible: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    estimated_tax_savings: Mapped[float] = mapped_column(
        Numeric(12, 2),
        default=0,
        comment="At assumed tax rate"
    )

    # Metadata
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    is_final: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Locked for auditor"
    )
    auditor_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self):
        return f"<TaxReportModel(period='{self.period_start}:{self.period_end}', total={self.total_discounts})>"


# ================================================================
# FREE ITEM TRACKER - The lights, the WiFi, the little things
# ================================================================

class FreeItemTrackerModel(Base):
    """
    Track ALL the free stuff in the shop.

    Free lights. Free WiFi. Free newspapers.
    Free water for dogs. Free smiles.

    It all has value. Track it.
    """
    __tablename__ = 'free_item_trackers'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # What's free
    item_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Newspaper, WiFi, Water bowl, Charging"
    )
    item_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="amenity, service, consumable"
    )

    # Value estimation
    estimated_unit_cost: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        comment="What it costs us per use"
    )
    estimated_value_to_customer: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        comment="What customer would pay elsewhere"
    )

    # Usage tracking
    is_tracked_daily: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Do we count usage?"
    )
    daily_usage_estimate: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Estimated uses per day"
    )

    # Tax treatment
    tax_category: Mapped[TaxCategory] = mapped_column(
        SQLEnum(TaxCategory),
        default=TaxCategory.PROMOTIONAL_EXPENSE
    )
    include_in_reports: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Include in tax reports?"
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<FreeItemTrackerModel(name='{self.item_name}', cost={self.estimated_unit_cost})>"


# ================================================================
# DEFAULT DISCOUNT REASONS - Andy's Quick Buttons
# ================================================================

DEFAULT_DISCOUNT_REASONS = [
    {
        "name": "Landlord Meeting",
        "code": "LANDLORD",
        "discount_type": DiscountType.COMP_OWNER,
        "tax_category": TaxCategory.ENTERTAINMENT,
        "default_percentage": 100,
        "description": "Boris and friends - part of doing business"
    },
    {
        "name": "Vendor Meeting",
        "code": "VENDOR",
        "discount_type": DiscountType.COMP_OWNER,
        "tax_category": TaxCategory.ENTERTAINMENT,
        "default_percentage": 100,
        "description": "Marco, suppliers - business relationship"
    },
    {
        "name": "Staff Meal",
        "code": "STAFF",
        "discount_type": DiscountType.COMP_STAFF,
        "tax_category": TaxCategory.STAFF_BENEFIT,
        "default_percentage": 100,
        "description": "Andy, Alee, Gerry meals on shift"
    },
    {
        "name": "Staff Coffee",
        "code": "STAFFCOF",
        "discount_type": DiscountType.COMP_STAFF,
        "tax_category": TaxCategory.STAFF_BENEFIT,
        "default_percentage": 100,
        "description": "Staff coffees during shift"
    },
    {
        "name": "VIP Customer",
        "code": "VIP",
        "discount_type": DiscountType.COMP_VIP,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 100,
        "description": "Special customers, influencers"
    },
    {
        "name": "First Visit",
        "code": "FIRST",
        "discount_type": DiscountType.PROMO_NEW_CUSTOMER,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 100,
        "description": "First coffee free for new customers"
    },
    {
        "name": "Grand Opening",
        "code": "OPENING",
        "discount_type": DiscountType.PROMO_EVENT,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 100,
        "description": "Day One specials"
    },
    {
        "name": "Product Sample",
        "code": "SAMPLE",
        "discount_type": DiscountType.SAMPLE_PRODUCT,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 100,
        "description": "New product tasting"
    },
    {
        "name": "Made Wrong",
        "code": "REMAKE",
        "discount_type": DiscountType.COMP_DAMAGE,
        "tax_category": TaxCategory.COST_OF_GOODS,
        "default_percentage": 100,
        "description": "Had to remake, gave original free"
    },
    {
        "name": "Expired Product",
        "code": "EXPIRED",
        "discount_type": DiscountType.WASTE_EXPIRED,
        "tax_category": TaxCategory.COST_OF_GOODS,
        "default_percentage": 100,
        "description": "Past sell-by date"
    },
    {
        "name": "Michel Waste",
        "code": "MICHEL",
        "discount_type": DiscountType.WASTE_MICHEL,
        "tax_category": TaxCategory.COST_OF_GOODS,
        "default_percentage": 100,
        "description": "Michel used whole bottle again"
    },
    {
        "name": "Member 5%",
        "code": "MEM5",
        "discount_type": DiscountType.MEMBER_REGULAR,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 5,
        "description": "Regular member discount"
    },
    {
        "name": "Member 10%",
        "code": "MEM10",
        "discount_type": DiscountType.MEMBER_JACK,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 10,
        "description": "Jack in the Box member"
    },
    {
        "name": "Member 15%",
        "code": "MEM15",
        "discount_type": DiscountType.MEMBER_VIP,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 15,
        "description": "VIP member"
    },
    {
        "name": "Founder 20%",
        "code": "FOUNDER",
        "discount_type": DiscountType.MEMBER_FOUNDER,
        "tax_category": TaxCategory.PROMOTIONAL_EXPENSE,
        "default_percentage": 20,
        "description": "Day One founder member"
    },
]


# ================================================================
# DEFAULT FREE ITEMS - The little things
# ================================================================

DEFAULT_FREE_ITEMS = [
    {
        "item_name": "WiFi Access",
        "item_category": "amenity",
        "estimated_unit_cost": 0.10,
        "estimated_value_to_customer": 2.00,
        "daily_usage_estimate": 20,
    },
    {
        "item_name": "Newspaper Browse",
        "item_category": "amenity",
        "estimated_unit_cost": 0.50,
        "estimated_value_to_customer": 3.00,
        "daily_usage_estimate": 10,
    },
    {
        "item_name": "Phone Charging",
        "item_category": "service",
        "estimated_unit_cost": 0.05,
        "estimated_value_to_customer": 1.00,
        "daily_usage_estimate": 5,
    },
    {
        "item_name": "Water for Dogs",
        "item_category": "consumable",
        "estimated_unit_cost": 0.10,
        "estimated_value_to_customer": 0.50,
        "daily_usage_estimate": 3,
    },
    {
        "item_name": "Restroom Access",
        "item_category": "amenity",
        "estimated_unit_cost": 0.20,
        "estimated_value_to_customer": 1.00,
        "daily_usage_estimate": 15,
    },
]


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def calculate_tax_savings(total_deductible: float, tax_rate: float = 0.20) -> float:
    """Calculate estimated tax savings at given rate"""
    return round(total_deductible * tax_rate, 2)


def get_discount_ratio(discounts: float, revenue: float) -> float:
    """Calculate discount as percentage of revenue"""
    if revenue <= 0:
        return 0.0
    return round((discounts / revenue) * 100, 2)
