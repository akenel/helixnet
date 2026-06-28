"""POS in-app notifications — the reporter BELL (Hypercare PoC-3).

When the AI triages a user's feedback ticket, the reporter gets a quiet little notification
("we're on it") by their name — they never see the AI cockpit, just the magic. One row per
event, addressed to a username. New table → created by create_all on startup (no migration).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class POSNotificationModel(Base):
    """A single in-app notification addressed to one POS user (by username)."""
    __tablename__ = "pos_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Username this notification is for (BacklogItem.created_by)")
    kind: Mapped[str] = mapped_column(
        String(30), nullable=False, default="triaged",
        comment="triaged | opened | confirm | shipped")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Backlog item number (BL-NNN) this is about")
    link: Mapped[str | None] = mapped_column(
        String(300), nullable=True, comment="Where the bell sends the user on click")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc), index=True)
