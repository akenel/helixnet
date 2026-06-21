# File: src/db/models/cash_shift_model.py
"""
Cash Shift - per-cashier drawer accountability (the lockbox model).

How a real till works, modelled honestly:
  1. Cashier OPENS a shift by counting the float into THEIR drawer
     (e.g. "two 50s + coins = CHF 100.55"). That's the starting amount.
  2. They ring sales (every transaction already carries cashier_id).
  3. Mid-shift cash that isn't a sale -- petty cash out, a float top-up in --
     is a recorded paid-in / paid-out with a reason (so the count can balance).
  4. Cashier CLOSES by counting the drawer. The system computes the EXPECTED
     cash (float + cash sales + paid-in - paid-out - cash refunds) and the
     VARIANCE (counted - expected). Within tolerance (default CHF 0.20) = green;
     outside = flagged with a required note.

This is its OWN model, separate from ShiftSessionModel (which tracks login
presence/handoff). A cash shift is the money story; the session is the who's-
logged-in story. open_at/closed_at also give clean shift hours.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Text, Integer, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.constants import HelixEnum
from .base import Base


class CashShiftStatus(HelixEnum):
    """A cash shift is either taking sales or counted-out and closed."""
    OPEN = "open"
    CLOSED = "closed"


class CashMovementKind(HelixEnum):
    """Non-sale cash that moves in or out of the drawer mid-shift."""
    PAID_IN = "paid_in"      # float top-up, change brought in
    PAID_OUT = "paid_out"    # petty cash, supplier paid from drawer


class CashShiftModel(Base):
    """One cashier's drawer, from float-in to count-out."""
    __tablename__ = "cash_shifts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    # Who owns this drawer + where.
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True,
        comment="Keycloak sub / username of the cashier who owns this shift")
    username: Mapped[str] = mapped_column(String(100), nullable=False,
        comment="Display name (pam, ralph, felix)")
    store_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    register_id: Mapped[str | None] = mapped_column(String(20), nullable=True,
        comment="Physical register/drawer if more than one (REG-01)")

    status: Mapped[CashShiftStatus] = mapped_column(
        SQLEnum(CashShiftStatus, name="cash_shift_status", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=CashShiftStatus.OPEN, index=True)

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        comment="Float counted in -> shift start (and clock-in)")
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Drawer counted out -> shift end (and clock-out)")

    # --- Opening: the float ---
    opening_float: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="Cash counted into the drawer at open (CHF)")
    opening_denoms: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="JSON denomination breakdown at open {\"50\":2,\"0.05\":11}")

    # --- Closing: the count + the math (all snapshotted at close) ---
    cash_sales: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash taken from sales during the shift (this cashier)")
    cash_refunds: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash refunded during the shift (this cashier)")
    card_sales: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Non-cash sales (visa/twint/debit) -- reported, NOT in the drawer")
    paid_in_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="Sum of non-sale cash brought in")
    paid_out_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0,
        comment="Sum of non-sale cash taken out")

    expected_cash: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="float + cash_sales + paid_in - paid_out - cash_refunds")
    counted_cash: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="Cash actually counted in the drawer at close")
    closing_denoms: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="JSON denomination breakdown at close")
    variance: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True,
        comment="counted_cash - expected_cash (negative = short)")
    tolerance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.20,
        comment="Acceptable |variance| before it's flagged (CHF)")
    within_tolerance: Mapped[bool | None] = mapped_column(Boolean, nullable=True,
        comment="abs(variance) <= tolerance")
    variance_note: Mapped[str | None] = mapped_column(Text, nullable=True,
        comment="Required explanation when outside tolerance")

    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
        comment="Completed transactions rung during this shift")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    movements: Mapped[list["CashMovementModel"]] = relationship(
        back_populates="shift", cascade="all, delete-orphan",
        order_by="CashMovementModel.created_at")


class CashMovementModel(Base):
    """An audited paid-in / paid-out -- every non-sale cash move carries a reason."""
    __tablename__ = "cash_movements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_shifts.id", ondelete="CASCADE"),
        nullable=False, index=True)
    kind: Mapped[CashMovementKind] = mapped_column(
        SQLEnum(CashMovementKind, name="cash_movement_kind", create_constraint=True,
                values_callable=lambda x: [e.value for e in x]),
        nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False,
        comment="Always positive; kind says in or out")
    reason: Mapped[str] = mapped_column(String(300), nullable=False,
        comment="Why the cash moved (petty cash: milk, float top-up)")
    actor: Mapped[str] = mapped_column(String(100), nullable=False,
        comment="Who recorded it")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    shift: Mapped["CashShiftModel"] = relationship(back_populates="movements")
