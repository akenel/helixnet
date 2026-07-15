# File: src/db/models/customer_model.py
"""
CustomerModel - The CRACK Profile

"Knowledge is the gold" - KB-001

Every customer is a potential CRACK (Cannabis Revolutionary And Community Keeper).
This model tracks both spending (loyalty tiers) and knowledge contributions (CRACK levels).

BLQ: One model, two progression paths, infinite possibilities.
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from src.core.constants import HelixEnum
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class CrackLevel(HelixEnum):
    """CRACK progression - from curious to oracle"""
    SEEDLING = "seedling"      # Just joined, learning the way
    SPROUT = "sprout"          # First KB written - started contributing
    ROOTED = "rooted"          # 5+ KBs - established contributor
    GROWING = "growing"        # 10+ KBs - mentoring others
    BLAZING = "blazing"        # 25+ KBs - community leader
    ORACLE = "oracle"          # Masters (Mosey, Felix level)


class LoyaltyTier(HelixEnum):
    """Spending-based tiers - auto-calculated from lifetime spend"""
    BRONZE = "bronze"          # 0-199 CHF → 5% discount
    SILVER = "silver"          # 200-499 CHF → 10% discount
    GOLD = "gold"              # 500-999 CHF → 15% discount
    PLATINUM = "platinum"      # 1000-2499 CHF → 20% discount
    DIAMOND = "diamond"        # 2500+ CHF → 25% + VIP perks


class PreferredContact(HelixEnum):
    """How does this CRACK want to be reached?"""
    EMAIL = "email"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    NONE = "none"              # Privacy first - respect it


class CustomerModel(Base):
    """
    The heart of HelixNETWORK loyalty.

    Two paths to rewards:
    1. Spend money → Earn credits + tier discounts
    2. Share knowledge → Earn credits + CRACK level

    Credits are universal currency - earned both ways, spent same way.
    """
    __tablename__ = 'customers'

    # ================================================================
    # PRIMARY KEY
    # ================================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # ================================================================
    # IDENTITY - The "Larry/Poppie" Problem Solved
    # ================================================================
    handle: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Public handle - how they're known (Poppie)"
    )
    real_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Private name - only for staff (Larry)"
    )

    # ================================================================
    # QR CODE - Rapid Checkout (BLQ Scene: Coolie shows QR, Pam scans)
    # ================================================================
    qr_code: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=True,
        comment="Unique QR code for rapid customer lookup (HLX-XXXXXXXX)"
    )

    # ================================================================
    # CONTACT - Multiple channels, one preference
    # ================================================================
    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
        comment="Email address"
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Phone number (+41 format)"
    )
    instagram: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
        comment="Instagram handle (@poppie_420)"
    )
    telegram: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Telegram handle (@poppie)"
    )
    whatsapp: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="WhatsApp number"
    )
    preferred_contact: Mapped[PreferredContact] = mapped_column(
        SQLEnum(PreferredContact),
        default=PreferredContact.INSTAGRAM,
        nullable=False,
        comment="How to reach this CRACK"
    )

    # ================================================================
    # PERSONAL
    # ================================================================
    birthday: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Birthday for 2x points during birthday week"
    )
    language: Mapped[str] = mapped_column(
        String(5),
        default="de",
        nullable=False,
        comment="Preferred language (de/en/fr/it)"
    )

    # ================================================================
    # LOYALTY TIER - Spending-based progression
    # ================================================================
    loyalty_tier: Mapped[LoyaltyTier] = mapped_column(
        SQLEnum(LoyaltyTier),
        default=LoyaltyTier.BRONZE,
        nullable=False,
        comment="Current spending tier"
    )
    lifetime_spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Total CHF spent all time"
    )
    tier_discount_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current standing discount % (Banco 3-tier: Bronze 0 / Silver 5 / Gold 10)"
    )
    tier_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        comment="True = tier was MANUALLY set (override); recalculate_tier keeps it, only the % tracks settings"
    )

    # ================================================================
    # CREDITS - The Universal Currency
    # ================================================================
    credits_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current spendable credits"
    )
    credits_earned_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="All-time credits earned"
    )
    credits_spent_total: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="All-time credits redeemed"
    )

    # ================================================================
    # CRACK LEVEL - Knowledge contribution progression
    # ================================================================
    crack_level: Mapped[CrackLevel] = mapped_column(
        SQLEnum(CrackLevel),
        default=CrackLevel.SEEDLING,
        nullable=False,
        comment="Current knowledge level"
    )
    crack_group: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="CRACK group number (Group 7, etc.)"
    )
    crack_team: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="CRACK team name (Pink Punch Squad)"
    )

    # ================================================================
    # KB CONTRIBUTIONS
    # ================================================================
    kbs_written: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total KBs written"
    )
    kbs_approved: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="KBs approved and live"
    )
    kbs_featured: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="KBs featured (hall of fame)"
    )
    kb_credits_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Credits earned from KB contributions"
    )

    # ================================================================
    # ACTIVITY TRACKING
    # ================================================================
    first_purchase: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="First purchase date"
    )
    last_purchase: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Most recent purchase"
    )
    last_visit: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last store visit"
    )
    visit_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total store visits"
    )
    purchase_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total purchases made"
    )
    average_basket: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Average transaction value"
    )

    # ================================================================
    # PREFERENCES - JSON for flexibility
    # ================================================================
    favorite_products: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="List of favorite product SKUs"
    )
    favorite_categories: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="Preferred product categories"
    )

    # ================================================================
    # REFERRALS
    # ================================================================
    referrer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Who referred this CRACK"
    )
    referrals_made: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="How many CRACKs they've referred"
    )
    referral_credits_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Credits earned from referrals"
    )

    # ================================================================
    # STAFF NOTES
    # ================================================================
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Internal staff notes (private)"
    )

    # ================================================================
    # STATUS
    # ================================================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Account active"
    )
    is_vip: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="VIP status (manual, for special cases)"
    )

    # ================================================================
    # COMPLIANCE & CONSENT (the only must: 18+)
    # ================================================================
    age_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="18+ confirmed (ticked by staff at the counter / on online claim)"
    )
    # Real, full date of birth (NOT the marketing 'birthday' above). This is the
    # authoritative age source for the 18+ gate: a member with a DOB auto-rolls over at
    # 18 and needs no re-confirmation. Nullable so EVERY existing member (who has
    # age_confirmed=True but no DOB) stays of-age via the back-compat rule in
    # customer_schema.member_of_age(). Also the field the birthday-rewards engine
    # (fast-follow, out of scope here) will ride.
    birthdate: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Full date of birth — authoritative 18+ age source (nullable; legacy members rely on age_confirmed)"
    )
    marketing_consent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Explicit opt-in for SMS/email offers (Swiss FADP -- default off)"
    )

    # ================================================================
    # WELCOME / FIRST-ORDER DISCOUNT (kiosk self-signup — banco-kiosk-guest-station)
    # A one-time discount a guest earns by becoming a member at the kiosk (10%) or on their
    # own phone (15%). Applied ONCE on the first order, then `used` flips true. Separate from
    # the standing loyalty tier_discount_percent — this is the join-today hook.
    # ================================================================
    welcome_discount_pct: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="One-time first-order discount % earned at signup (0 = none)"
    )
    welcome_discount_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True once the welcome discount has been redeemed on an order"
    )
    signup_source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Where they enrolled: kiosk / phone / staff — drives the discount + Felix's 'new today' list"
    )

    # ================================================================
    # TIMESTAMPS
    # ================================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ================================================================
    # RELATIONSHIPS
    # ================================================================
    kb_contributions: Mapped[list["KBContributionModel"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan"
    )
    credit_transactions: Mapped[list["CreditTransactionModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    # ================================================================
    # TIER CALCULATION
    # ================================================================
    @property
    def is_of_age(self) -> bool:
        """True iff this member may buy 18+ lines. Rule (back-compat critical):
        of_age = (birthdate present AND >=18) OR (birthdate absent AND age_confirmed).
        Delegates to the pure policy in customer_schema so the rule lives in one place."""
        from src.schemas.customer_schema import member_of_age
        return member_of_age(self.birthdate, self.age_confirmed)

    def recalculate_tier(self, policy=None) -> None:
        """Update tier from lifetime spend via the loyalty policy. `policy` = the rungs from the
        store's Settings → Discounts (Felix owns the thresholds + %); None falls back to the
        conservative code defaults. Bronze = points only; Silver/Gold/Platinum are configurable.

        If tier_locked (a MANUAL override), the tier NAME is left alone — spend can't demote or
        promote a hand-set member — but the % still tracks the current settings for that tier."""
        from src.services.loyalty_service import tier_for_spend, pct_for_tier
        if self.tier_locked:
            self.tier_discount_percent = pct_for_tier(self.loyalty_tier.value, policy)
            return
        name, pct = tier_for_spend(self.lifetime_spend, policy)
        self.loyalty_tier = LoyaltyTier(name)
        self.tier_discount_percent = pct

    def recalculate_crack_level(self) -> None:
        """Update CRACK level based on approved KBs"""
        kbs = self.kbs_approved
        if kbs >= 25:
            self.crack_level = CrackLevel.BLAZING
        elif kbs >= 10:
            self.crack_level = CrackLevel.GROWING
        elif kbs >= 5:
            self.crack_level = CrackLevel.ROOTED
        elif kbs >= 1:
            self.crack_level = CrackLevel.SPROUT
        else:
            self.crack_level = CrackLevel.SEEDLING

    def generate_qr_code(self) -> str:
        """Generate unique QR code for rapid checkout: HLX-XXXXXXXX"""
        import secrets
        code = f"HLX-{secrets.token_hex(4).upper()}"
        self.qr_code = code
        return code

    def __repr__(self):
        return f"<CustomerModel(handle='{self.handle}', tier={self.loyalty_tier.value}, crack={self.crack_level.value})>"
