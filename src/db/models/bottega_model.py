# File: src/db/models/bottega_model.py
# Purpose: A user's Bottega profile -- built/enriched from their CV (cv-to-bio).
# Enrich-safely: before any apply, the prior profile is snapshotted to history so
# nothing is ever silently clobbered (always recoverable / undo).

from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text
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
