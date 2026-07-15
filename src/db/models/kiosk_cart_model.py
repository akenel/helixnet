# File: src/db/models/kiosk_cart_model.py
"""
KioskCartModel — a guest's HELD ORDER from the kiosk (banco-kiosk-guest-station, v2).

The McDonald's-kiosk flow: a guest builds a basket at the kiosk (or on their own phone via the
QR), gets a short human CODE ("A7K3"), and walks it to the counter. Felix pulls the order up by
that code and rings it out — the guest already did the picking while he was busy.

Items are a PRICE-SNAPSHOT (what the guest saw). The authoritative catalogue price is always
re-checked when Felix actually rings the sale (create_sale) — the snapshot is for display only.
A NEW table, so create_all() builds it; no ALTER needed.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class KioskCartModel(Base):
    __tablename__ = 'kiosk_carts'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Short, human, shout-across-the-counter code ("A7K3"). Unique + indexed = fast retrieval.
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)

    # The member who built it, if they signed up (drives the welcome discount). Nullable —
    # a guest can build a cart without joining.
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True)

    # [{product_id, name, price, qty}] — a display snapshot; real price re-checked at checkout.
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # open = waiting at the counter · claimed = Felix rang it · void = abandoned/cancelled
    status: Mapped[str] = mapped_column(String(12), default='open', index=True, nullable=False)

    source: Mapped[str | None] = mapped_column(String(20), nullable=True)   # kiosk | phone
    lang: Mapped[str] = mapped_column(String(5), default='de', nullable=False)

    claimed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
