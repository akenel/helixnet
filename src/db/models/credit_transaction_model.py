# File: src/db/models/credit_transaction_model.py
"""
CreditTransactionModel - The Ledger of Credits

Every credit earned or spent is recorded here.
Immutable audit trail for the gamification system.

BLQ: Track everything, question nothing. The numbers don't lie.
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, DateTime, Integer, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class CreditTransactionType(str, Enum):
    """How were credits earned or spent?"""
    # Earning
    PURCHASE = "purchase"              # 1 credit per CHF spent
    REFERRAL = "referral"              # 100 for referrer, 50 for new
    KB_SUBMITTED = "kb_submitted"      # 10 for trying
    KB_APPROVED = "kb_approved"        # 100 base
    KB_PUBLISHED = "kb_published"      # 50 bonus
    KB_FEATURED = "kb_featured"        # 250 bonus
    KB_REVIEW = "kb_review"            # 25 for reviewing others
    KB_BONUS_IMAGES = "kb_bonus_images"    # +25
    KB_BONUS_VIDEO = "kb_bonus_video"      # +50
    KB_BONUS_BOM = "kb_bonus_bom"          # +75
    KB_BONUS_LAB = "kb_bonus_lab"          # +100
    ACTION_BONUS = "action_bonus"      # Profile completion, etc.
    BIRTHDAY_BONUS = "birthday_bonus"  # 2x during birthday week
    STREAK_BONUS = "streak_bonus"      # Weekly visit streak
    EVENT_PRIZE = "event_prize"        # HelixCup 2026, etc.

    # Spending
    REDEMPTION = "redemption"          # Voucher redemption
    GIFT = "gift"                      # Gifted to another CRACK

    # Adjustments
    ADJUSTMENT = "adjustment"          # Manual adjustment by owner
    EXPIRY = "expiry"                  # Credits expired (if policy exists)
    CORRECTION = "correction"          # Error correction


class CreditTransactionModel(Base):
    """
    Credit transaction ledger entry.

    Positive = earned, Negative = spent
    Balance calculated from running sum.
    """
    __tablename__ = 'credit_transactions'

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
    # CUSTOMER REFERENCE
    # ================================================================
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="The CRACK whose credits changed"
    )

    # ================================================================
    # TRANSACTION DETAILS
    # ================================================================
    transaction_type: Mapped[CreditTransactionType] = mapped_column(
        SQLEnum(CreditTransactionType),
        nullable=False,
        index=True,
        comment="Type of credit transaction"
    )
    credits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Credits earned (+) or spent (-)"
    )
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Balance after this transaction"
    )

    # ================================================================
    # REFERENCE - What triggered this?
    # ================================================================
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Related KB, order, event, etc."
    )
    reference_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Type: kb, order, event, referral, etc."
    )

    # ================================================================
    # DESCRIPTION
    # ================================================================
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Human-readable description"
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes (for adjustments)"
    )

    # ================================================================
    # AUDIT
    # ================================================================
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Who created this (for manual adjustments)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # ================================================================
    # RELATIONSHIPS
    # ================================================================
    customer: Mapped["CustomerModel"] = relationship(
        back_populates="credit_transactions"
    )

    def __repr__(self):
        sign = "+" if self.credits > 0 else ""
        return f"<CreditTransaction({sign}{self.credits} | {self.transaction_type.value} | bal={self.balance_after})>"
