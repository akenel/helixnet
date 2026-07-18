# File: src/payments/worldline.py
"""
🌍-1 M2 — the Worldline TIM adapter. Drives an ep2 terminal (Felix's AXIUM DX8000 /
Move/5000) to capture TWINT + cards, over a `TerminalLink` transport.

The provider stays DATA per store (like `_store_currency`): resolver registers
'worldline' → `get_payment_provider` returns this adapter. The transport is what changes
between the sim and the shop floor:

  • TODAY  — `MockTerminal` (in-memory, scriptable) → build + test with no hardware.
  • GO-LIVE — `TimTcpTerminalLink(host, port)` to the terminal IP Worldline gives us.

This adapter does NOT change between the two — that is the whole point of the seam.

NOT registered in resolver._ADAPTERS yet: registration is the go-live wiring, done when we
have the terminal IP + Worldline's confirmed spec, so a mis-set store can never reach a
half-built path (prove-don't-assume). Until then a store set to 'worldline' fails SAFE to
manual (see resolver). Full design: docs/SPEC-payments-seam.md §4.
"""
from __future__ import annotations

import asyncio
import logging

from .base import PaymentIntent, PaymentResult, PaymentStatus
from .mock_terminal import TerminalLink

logger = logging.getLogger(__name__)

# terminal wire status → our lifecycle enum
_STATUS = {
    "approved": PaymentStatus.APPROVED,
    "declined": PaymentStatus.DECLINED,
    "aborted": PaymentStatus.ABORTED,
    "pending": PaymentStatus.PENDING,
    "error": PaymentStatus.ERROR,
}


class WorldlineTIMAdapter:
    """`PaymentProvider` over a Worldline ep2/TIM terminal link.

    Satisfies the seam Protocol (name + initiate_payment/poll_status/cancel) and adds
    `charge()` — the full capture loop checkout will call in M2: never complete the sale
    until the terminal says APPROVED (else keep the cart for retry / cash).
    """

    name = "worldline"

    def __init__(self, terminal: TerminalLink):
        self._terminal = terminal
        # our idempotency key (intent_id) → the terminal's own session id
        self._sessions: dict[str, str] = {}

    async def initiate_payment(self, intent: PaymentIntent) -> str:
        """Open the reader and put the amount on the terminal. Returns the session id."""
        sid = await self._terminal.request_payment(
            amount_minor=intent.amount_minor,
            currency=intent.currency,
            reference=intent.reference,
        )
        self._sessions[intent.intent_id] = sid
        logger.info(
            "worldline: session %s opened for intent %s (%s %s ref=%s)",
            sid, intent.intent_id, intent.currency, intent.amount, intent.reference,
        )
        return sid

    async def poll_status(self, intent_id: str) -> PaymentResult:
        """Read the terminal's current state for this intent → a PaymentResult."""
        sid = self._sessions.get(intent_id)
        if sid is None:
            return PaymentResult(
                intent_id=intent_id, status=PaymentStatus.ERROR,
                raw={"reason": "unknown_intent"},
            )
        payload = await self._terminal.get_result(sid)
        status = _STATUS.get(payload.get("status", "error"), PaymentStatus.ERROR)
        return PaymentResult(
            intent_id=intent_id,
            status=status,
            provider_txn_id=payload.get("txn_id"),
            card_scheme=payload.get("scheme"),
            raw=payload,
        )

    async def cancel(self, intent_id: str) -> None:
        """Abort an in-flight charge (cashier escape / timeout)."""
        sid = self._sessions.get(intent_id)
        if sid is not None:
            await self._terminal.abort(sid)

    async def charge(
        self, intent: PaymentIntent, *, timeout: float = 60.0, poll_interval: float = 0.5,
    ) -> PaymentResult:
        """Full capture: initiate → poll until a terminal state or `timeout` seconds.

        This is the shape M2's `capture_on_terminal_if_configured` uses — the sale is only
        completed on APPROVED; DECLINED/ABORTED/TIMEOUT keep the cart for retry or cash. On
        timeout we also tell the terminal to stop so it can't approve after we've moved on.
        """
        await self.initiate_payment(intent)
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            result = await self.poll_status(intent.intent_id)
            if result.status != PaymentStatus.PENDING:
                return result
            await asyncio.sleep(poll_interval)
        await self.cancel(intent.intent_id)
        logger.warning("worldline: intent %s timed out after %ss", intent.intent_id, timeout)
        return PaymentResult(
            intent_id=intent.intent_id, status=PaymentStatus.TIMEOUT,
            raw={"reason": "no_terminal_response", "timeout_s": timeout},
        )


class TimTcpTerminalLink:
    """The REAL transport — a TCP/TIM client to the terminal at (host, port).

    Skeleton only. The ep2/TIM message framing gets filled in when Worldline delivers the
    spec (SPEC-payments-seam §4). Everything ABOVE this — WorldlineTIMAdapter, the checkout
    hook, receipts — is already built and unit-tested against MockTerminal, so go-live is:
    implement these three methods against the terminal socket and register 'worldline'.
    """

    def __init__(self, host: str, port: int = 7784, *, tid: str):
        self.host = host
        self.port = port
        self.tid = tid

    async def request_payment(self, *, amount_minor: int, currency: str, reference: str) -> str:
        raise NotImplementedError("Worldline TIM wire format pending spec (SPEC-payments-seam §4)")

    async def get_result(self, session_id: str) -> dict:
        raise NotImplementedError("Worldline TIM wire format pending spec (SPEC-payments-seam §4)")

    async def abort(self, session_id: str) -> None:
        raise NotImplementedError("Worldline TIM wire format pending spec (SPEC-payments-seam §4)")
