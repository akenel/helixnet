# File: src/db/models/qa_test_result_model.py
# Purpose: QA Testing Dashboard models -- Anne's testing checklist + bug reports

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from .base import Base


# ================================================================
# Enums
# ================================================================
class TestStatus(str, enum.Enum):
    """Status of a single test item."""
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    BLOCKED = "blocked"


class BugSeverity(str, enum.Enum):
    """Bug severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugStatus(str, enum.Enum):
    """Bug lifecycle status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    WONT_FIX = "wont_fix"


# ================================================================
# QA Test Result Model
# ================================================================
class QATestResultModel(Base):
    __tablename__ = "qa_test_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    phase: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Phase number (1-9)",
    )
    phase_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Phase display name (e.g. 'First Login')",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order within phase for display",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Test item title",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed test instructions",
    )
    status: Mapped[TestStatus] = mapped_column(
        SQLEnum(TestStatus, name="qa_test_status", create_constraint=True),
        nullable=False,
        default=TestStatus.PENDING,
        index=True,
        comment="Current test status",
    )
    tester_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Who executed this test",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Tester notes or observations",
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the test was executed",
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
    bug_reports: Mapped[list["QABugReportModel"]] = relationship(
        back_populates="test_result",
        cascade="all, delete-orphan",
    )


# ================================================================
# QA Bug Report Model
# ================================================================
class QABugReportModel(Base):
    __tablename__ = "qa_bug_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Bug title",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="What happened and what was expected",
    )
    severity: Mapped[BugSeverity] = mapped_column(
        SQLEnum(BugSeverity, name="qa_bug_severity", create_constraint=True),
        nullable=False,
        default=BugSeverity.MEDIUM,
        index=True,
        comment="Bug severity level",
    )
    status: Mapped[BugStatus] = mapped_column(
        SQLEnum(BugStatus, name="qa_bug_status", create_constraint=True),
        nullable=False,
        default=BugStatus.OPEN,
        index=True,
        comment="Bug lifecycle status",
    )
    test_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_test_results.id"),
        nullable=True,
        comment="Optional link to the test that found this bug",
    )
    screenshot_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to screenshot",
    )
    browser_info: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Browser/device info",
    )
    reported_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Anne",
        comment="Who reported this bug",
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
    test_result: Mapped["QATestResultModel | None"] = relationship(
        back_populates="bug_reports",
        foreign_keys=[test_result_id],
    )
