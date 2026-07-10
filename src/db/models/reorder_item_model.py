# File: src/db/models/reorder_item_model.py
# Purpose: BL-21/22 — the "Order Book". The digital pencil-list the shop reorders from.
#
# Doctrine (docs/BANCO-REORDER-ORDER-BOOK.md): Banco is ZERO-PERPETUAL — we never compute
# reorder from an on-hand count (it's a lie). The Order Book leans on what we DO know:
# sales velocity (suggest) + order STATE (to_order → on_order → received) + the human eyeball.
# It SUGGESTS, never decides. BL-22: each line carries the supplier the human PICKED for it
# (one product can be ordered from several suppliers — 420 because it's on the next shipment,
# Wellauer because it's cheaper). Status/reason are plain strings on purpose — lighter than a
# PG enum type and no enum-casing drift.

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

# Allowed values (validated in the schema layer; kept as strings in the DB).
REORDER_REASONS = ("restock", "customer_request")
REORDER_STATUSES = ("to_order", "on_order", "received", "cancelled")


class ReorderItemModel(Base):
    __tablename__ = "reorder_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Catalog item if it's a known product; NULL for a free-typed "we don't stock this yet" line.
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True, index=True)
    # A snapshot / free-text label so the line reads well even if the product is renamed or NULL.
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # restock | customer_request
    reason: Mapped[str] = mapped_column(String(20), nullable=False, default="restock", index=True)

    # Customer special-order ("Larry wanted the extra thing") — optional link + free note.
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # BL-22: which supplier the human picked for THIS line (a code from suppliers.code, e.g. "420").
    supplier_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    # to_order → on_order → received (or cancelled).
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="to_order", index=True)
    eta: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False)
