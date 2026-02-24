# File: src/db/models/isotto_activity_model.py
"""
IsottoOrderActivityModel - Append-only audit trail for ISOTTO Sport print orders.
Every status change, assignment, comment, payment -- timestamped, attributed.

Same proven pattern as ServiceJobActivityModel, QABugActivityModel, BacklogActivityModel.

"If one seal fails, check all the seals."
"""
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.core.constants import HelixEnum

from .base import Base


class IsottoActivityType(HelixEnum):
    """What happened to this order"""
    STATUS_CHANGE = "status_change"
    ASSIGNED = "assigned"
    COMMENT = "comment"
    PAYMENT = "payment"
    PROOF_APPROVED = "proof_approved"
    PRIORITY_CHANGE = "priority_change"
    INVOICE_CREATED = "invoice_created"


class IsottoOrderActivityModel(Base):
    """
    Append-only audit trail for print orders at ISOTTO Sport.
    Every status change, assignment, comment, payment -- timestamped, attributed.
    Same proven pattern as ServiceJobActivityModel.
    """
    __tablename__ = "isotto_order_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("isotto_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[IsottoActivityType] = mapped_column(
        SQLEnum(IsottoActivityType, name="isotto_activity_type", create_constraint=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Who performed this action",
    )
    old_value: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Previous value (old status, old assignee)",
    )
    new_value: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="New value (new status, new assignee)",
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Comment text or additional context",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    order: Mapped["IsottoOrderModel"] = relationship(
        back_populates="activities",
        foreign_keys=[order_id],
    )

    def __repr__(self):
        return f"<IsottoActivity(order={self.order_id}, type={self.activity_type}, actor='{self.actor}')>"
