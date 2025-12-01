# File: src/db/models/kb_contribution_model.py
"""
KBContributionModel - Knowledge Base Articles

"A KB is almost priceless if it explains how to distill 2ml of coconut extracts
for the CBD tanning butter" - The Angel

Every KB is a gift to the community. Contributors earn credits based on quality:
- Base: 100 credits
- With images: +25
- With video: +50
- With BOM/Recipe: +75
- With lab report: +100
- Featured bonus: +250

BLQ: Knowledge flows like water - capture it, reward it, share it.
"""
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import String, DateTime, Numeric, Integer, Boolean, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


class KBStatus(str, Enum):
    """KB approval workflow - from draft to glory"""
    DRAFT = "draft"            # CRACK is writing
    SUBMITTED = "submitted"    # Ready for review
    IN_REVIEW = "in_review"    # CRACKs reviewing
    APPROVED = "approved"      # Owner approved
    PUBLISHED = "published"    # Live in system
    REJECTED = "rejected"      # Needs revision
    ARCHIVED = "archived"      # No longer relevant


class KBCategory(str, Enum):
    """What kind of knowledge?"""
    RECIPE = "recipe"          # How to make something (CBD butter, tinctures)
    PROTOCOL = "protocol"      # How to use something (sleep protocol, dosing)
    GUIDE = "guide"            # How to do something (grinder maintenance)
    REVIEW = "review"          # Product review
    STRAIN = "strain"          # Strain information
    LAB = "lab"                # Lab reports and analysis
    STORY = "story"            # Personal journey/testimonial
    EVENT = "event"            # Event report (HelixCup, etc.)


class KBContributionModel(Base):
    """
    Knowledge Base Article - The currency of CRACKs.

    Jack Herer's vision: Knowledge should be free and shared.
    Our twist: Reward those who share with credits and recognition.
    """
    __tablename__ = 'kb_contributions'

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
    # AUTHOR - Who wrote this?
    # ================================================================
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('customers.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="The CRACK who wrote this"
    )

    # ================================================================
    # CONTENT IDENTITY
    # ================================================================
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="KB title (CBD Tanning Butter - Coconut Extract Method)"
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-friendly slug (cbd-tanning-butter-coconut)"
    )
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Brief description (what this KB teaches)"
    )
    category: Mapped[KBCategory] = mapped_column(
        SQLEnum(KBCategory),
        default=KBCategory.GUIDE,
        nullable=False,
        index=True,
        comment="KB category"
    )

    # ================================================================
    # CONTENT STORAGE
    # ================================================================
    content_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to markdown file in debllm/notes/"
    )
    content_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Rendered HTML content (cached)"
    )

    # ================================================================
    # QUALITY FLAGS - Affect credit calculation
    # ================================================================
    has_images: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="+25 credits if true"
    )
    has_video: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="+50 credits if true"
    )
    has_bom: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Bill of Materials / Recipe (+75 credits)"
    )
    has_lab_report: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Lab tested formula (+100 credits)"
    )

    # ================================================================
    # JACK HERER REFERENCE
    # ================================================================
    jh_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="JH chapter reference (JH-Chapter-8)"
    )
    jh_quote: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Relevant Jack Herer quote"
    )

    # ================================================================
    # WORKFLOW STATUS
    # ================================================================
    status: Mapped[KBStatus] = mapped_column(
        SQLEnum(KBStatus),
        default=KBStatus.DRAFT,
        nullable=False,
        index=True,
        comment="Current workflow status"
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When submitted for review"
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Who approved this KB (owner)"
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When approved"
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When published"
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When rejected"
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why it was rejected (feedback)"
    )

    # ================================================================
    # PEER REVIEW - CRACKs reviewing CRACKs
    # ================================================================
    reviewer_ids: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="List of reviewer UUIDs"
    )
    review_scores: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Reviewer scores {uuid: {rating, recommend, comment}}"
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of reviews"
    )
    rating_average: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
        nullable=False,
        comment="Average rating (1-5)"
    )
    recommend_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="How many recommend approval"
    )

    # ================================================================
    # CREDITS
    # ================================================================
    base_credits: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="Base credits for approval"
    )
    bonus_credits: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Quality bonuses (images, video, etc.)"
    )
    total_credits: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total credits awarded"
    )
    credits_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Credits already awarded to author"
    )

    # ================================================================
    # FEATURED
    # ================================================================
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Featured KB (hall of fame)"
    )
    featured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When featured"
    )
    featured_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Who featured it"
    )

    # ================================================================
    # STATS
    # ================================================================
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="How many times viewed"
    )
    share_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="How many times shared"
    )
    bookmark_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="How many CRACKs bookmarked"
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
    author: Mapped["CustomerModel"] = relationship(
        back_populates="kb_contributions"
    )

    # ================================================================
    # CREDIT CALCULATION
    # ================================================================
    def calculate_credits(self) -> int:
        """Calculate total credits based on quality flags"""
        credits = self.base_credits  # 100 base

        if self.has_images:
            credits += 25
        if self.has_video:
            credits += 50
        if self.has_bom:
            credits += 75
        if self.has_lab_report:
            credits += 100
        if self.is_featured:
            credits += 250

        self.bonus_credits = credits - self.base_credits
        self.total_credits = credits
        return credits

    def __repr__(self):
        return f"<KBContributionModel(title='{self.title}', status={self.status.value}, credits={self.total_credits})>"
