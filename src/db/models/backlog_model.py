# File: src/db/models/backlog_model.py
# Purpose: Unified Backlog -- one board for dev tasks, bug fixes, camper jobs, business ops

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, Text, Date, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base
from src.core.constants import HelixEnum, HelixApplication


# ================================================================
# Enums (HelixEnum = case-insensitive, lowercase values)
# ================================================================
class BacklogItemType(HelixEnum):
    """What kind of work is this."""
    DEV_TASK = "dev_task"
    BUG_FIX = "bug_fix"
    CAMPER_JOB = "camper_job"
    BUSINESS_OPS = "business_ops"


class BacklogStatus(HelixEnum):
    """Kanban column status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    ARCHIVED = "archived"


class BacklogPriority(HelixEnum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BacklogActivityType(HelixEnum):
    """What kind of activity happened on a backlog item."""
    STATUS_CHANGE = "status_change"
    ASSIGNED = "assigned"
    PRIORITY_CHANGE = "priority_change"
    COMMENT = "comment"


# ================================================================
# Backlog Item Model
# ================================================================
class BacklogItemModel(Base):
    __tablename__ = "backlog_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    item_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        comment="Human-readable item number (BL-001)",
    )
    item_type: Mapped[BacklogItemType] = mapped_column(
        SQLEnum(BacklogItemType, name="backlog_item_type", create_constraint=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BacklogItemType.DEV_TASK,
        index=True,
        comment="What kind of work: dev_task, bug_fix, camper_job, business_ops",
    )
    application: Mapped[HelixApplication] = mapped_column(
        SQLEnum(HelixApplication, name="helix_application", create_constraint=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=HelixApplication.HELIXNET,
        index=True,
        comment="Which app: helixnet, camper, isotto",
    )
    status: Mapped[BacklogStatus] = mapped_column(
        SQLEnum(BacklogStatus, name="backlog_status", create_constraint=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BacklogStatus.PENDING,
        index=True,
        comment="Kanban column: pending, in_progress, blocked, done, archived",
    )
    priority: Mapped[BacklogPriority] = mapped_column(
        SQLEnum(BacklogPriority, name="backlog_priority", create_constraint=True,
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BacklogPriority.MEDIUM,
        index=True,
        comment="Priority: low, medium, high, critical",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Item title",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the work",
    )
    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who currently owns this item",
    )
    due_date: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
        comment="Target completion date",
    )
    estimated_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Estimated hours of work",
    )
    blocked_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Why is this item blocked",
    )
    tags: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Comma-separated tags: postcard,isotto,urgent",
    )
    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Angel",
        comment="Who created this item",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    activities: Mapped[list["BacklogActivityModel"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="BacklogActivityModel.created_at",
    )


# ================================================================
# Backlog Activity Log (append-only)
# ================================================================
class BacklogActivityModel(Base):
    """Every status change, assignment, comment -- timestamped, attributed."""
    __tablename__ = "backlog_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("backlog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[BacklogActivityType] = mapped_column(
        SQLEnum(BacklogActivityType, name="backlog_activity_type", create_constraint=True,
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
    item: Mapped["BacklogItemModel"] = relationship(
        back_populates="activities",
        foreign_keys=[item_id],
    )
