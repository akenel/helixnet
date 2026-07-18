# File: src/db/models/payment_model.py
"""
PaymentModel — one row per electronic payment ATTEMPT against a terminal (🌍-1 seam).

A transaction can have several attempts (declined → retry); the APPROVED row is the
settlement of record. Cash / manual sales do NOT create rows here — those are captured on
the transaction itself (payment_method / amount_tendered). This table exists for terminal
settlements (Worldline TIM first, SumUp parked): the acquirer's txn id, the card scheme,
and the raw provider payload for reconciliation + refunds.

NEW table → created by create_all() on startup (and by conftest in tests); no ALTER needed.
The status is stored as the PaymentStatus value string (src.payments.base) — a plain
VARCHAR keeps it portable (SQLite tests + Postgres) and decoupled from the DB-enum churn.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), index=True, nullable=False,
        comment="The sale this payment settles")

    provider: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="Terminal provider: worldline | sumup | ...")

    # Our idempotency key for the attempt — a replayed capture adopts the same row instead of
    # double-charging. Unique among non-nulls (Postgres counts NULLs distinct).
    intent_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
        comment="Our idempotency key for this attempt")

    amount_minor: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Charged amount in integer minor units (Rappen/cents) — no float")
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="ISO currency (from _store_currency)")

    status: Mapped[str] = mapped_column(
        String(16), nullable=False,
        comment="PaymentStatus value: pending|approved|declined|aborted|timeout|error")

    provider_txn_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True,
        comment="Acquirer's own transaction id (refund / reconciliation)")
    card_scheme: Mapped[str | None] = mapped_column(
        String(24), nullable=True, comment="visa | mastercard | twint | … (receipt)")

    raw: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Full provider payload as JSON (audit) — heavy, portable")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When the provider confirmed approval")

    def __repr__(self):
        return (f"<PaymentModel(provider='{self.provider}', status='{self.status}', "
                f"amount_minor={self.amount_minor})>")
