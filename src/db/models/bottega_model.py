# File: src/db/models/bottega_model.py
# Purpose: A user's Bottega profile -- built/enriched from their CV (cv-to-bio).
# Enrich-safely: before any apply, the prior profile is snapshotted to history so
# nothing is ever silently clobbered (always recoverable / undo).

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, DateTime, Integer, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class BottegaProfileModel(Base):
    __tablename__ = "bottega_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="Keycloak username this profile belongs to",
    )
    slug: Mapped[str | None] = mapped_column(
        String(80), nullable=True, unique=True, index=True,
        comment="Public handle for /u/<slug>; defaults to slugified username",
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON array of skills extracted/confirmed",
    )
    categories: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON array of category slugs the user maps to",
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual",
        comment="cv | free | manual -- how this profile was built",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True,
        comment="draft (proposed, not yet confirmed) | applied (live)",
    )
    completeness: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Onboarding points 0-100 (gamified Pulse Check)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )
    journey_start: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="Day 1 of the 30-day-phase / 1-year journey (local date); null => use created_at",
    )


class BottegaSessionModel(Base):
    """A saved session in a user's Blueprint Folder (their cutover list). The QUESTION
    and the answer kept together, versioned -- a growing body of work the AI can read
    back as metadata for follow-ups."""
    __tablename__ = "bottega_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False,
                                      comment="recipe slug (e.g. mentor-session)")
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    inputs: Mapped[str] = mapped_column(Text, nullable=False, default="{}",
                                        comment="JSON of the inputs -- THE QUESTION")
    output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    output_type: Mapped[str] = mapped_column(String(16), nullable=False, default="markdown")
    tags: Mapped[str | None] = mapped_column(String(300), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
        comment="prior version (edit-and-rerun chains here)")
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
        comment="Ada's ledger: soft-delete tombstone -- hidden from view, never lost from history")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True)


class BottegaProfileHistoryModel(Base):
    """Append-only snapshot taken BEFORE each apply -- the undo / never-clobber log."""
    __tablename__ = "bottega_profile_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    snapshot: Mapped[str] = mapped_column(
        Text, nullable=False, comment="JSON of the prior profile (bio/tagline/skills/categories)",
    )
    reason: Mapped[str] = mapped_column(
        String(120), nullable=False, default="pre-apply snapshot",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False, index=True,
    )


class BottegaTaskModel(Base):
    """A daily one-pager task -- the member's habit-making checklist (Top 10 + Bonus Round).
    Keyed by the LOCAL date string it belongs to ('day'); move-to-tomorrow just changes the day.
    Lego-simple: a line, a checkbox, a note. For every man, woman, and child."""
    __tablename__ = "bottega_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    day: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="local date YYYY-MM-DD this task lives on")
    section: Mapped[str] = mapped_column(
        String(12), nullable=False, default="top10", comment="top10 | bonus")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="open", comment="open | done")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
