# File: src/payments/base.py
"""
🌍-1 Payments seam — the ONE place a card/TWINT terminal is driven from HelixPOS.

The provider is DATA per store (store_settings.payment_provider), exactly like the
currency seam (_store_currency): the POS core never hardcodes an acquirer. This module
defines the provider-agnostic contract; concrete adapters (Worldline TIM first — Felix's
existing ep2 terminal does TWINT + cards; SumUp Cloud parked) implement PaymentProvider
and register in resolver.py.

Money rule: amounts cross the seam as INTEGER minor units (Rappen/cents), quantized
first — never a float — so an imprecise 226.16999… can't truncate to the wrong charge
(the money-cent-precision discipline).

Full design: docs/SPEC-payments-seam.md.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from src.core.constants import HelixEnum


class PaymentStatus(HelixEnum):
    """Lifecycle of a single terminal payment attempt."""
    PENDING = "pending"     # sent to the terminal, waiting on the customer
    APPROVED = "approved"   # settled — the money moved
    DECLINED = "declined"   # card / TWINT refused
    ABORTED = "aborted"     # cashier or customer cancelled
    TIMEOUT = "timeout"     # the terminal never answered
    ERROR = "error"         # comms / provider fault


def to_minor_units(amount) -> int:
    """A money amount as an integer count of the currency's minor unit (Rappen/cents).

    Quantize to 2 dp FIRST (the money-cent-precision rule) so an imprecise Decimal like
    226.16999… becomes 226.17 → 22617, never a truncated 22616.
    """
    cents = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100
    return int(cents.to_integral_value(rounding=ROUND_HALF_UP))


class PaymentIntent(BaseModel):
    """What we ask a terminal to charge. Built once per attempt, on our side."""
    intent_id: str            # our idempotency key; also stored on the PaymentModel row
    provider: str             # "worldline" | "sumup" | ...
    amount_minor: int         # integer Rappen/cents — no float ever crosses the seam
    currency: str             # from _store_currency(db); never hardcode CHF
    reference: str            # the transaction number, shown on the slip

    @property
    def amount(self) -> Decimal:
        """The amount back as a 2 dp Decimal (display / receipts)."""
        return (Decimal(self.amount_minor) / Decimal(100)).quantize(Decimal("0.01"))


class PaymentResult(BaseModel):
    """What the terminal told us. `raw` keeps the full provider payload for audit."""
    intent_id: str
    status: PaymentStatus
    provider_txn_id: Optional[str] = None   # the acquirer's own id (refund / reconcile)
    card_scheme: Optional[str] = None       # visa / mastercard / twint … for the receipt
    raw: dict = Field(default_factory=dict)

    @property
    def approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED


@runtime_checkable
class PaymentProvider(Protocol):
    """A terminal adapter. Worldline TIM is the first implementation (M2)."""
    name: str

    async def initiate_payment(self, intent: PaymentIntent) -> str:
        """Start the charge on the terminal; return the provider's session id."""
        ...

    async def poll_status(self, intent_id: str) -> PaymentResult:
        """Fetch the current status (fallback when there's no push/webhook)."""
        ...

    async def cancel(self, intent_id: str) -> None:
        """Abort an in-flight charge."""
        ...
