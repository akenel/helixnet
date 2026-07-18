# File: src/payments/mock_terminal.py
"""
A mock ep2 / Worldline-TIM terminal — the "little terminal in the computer".

Stands in for Felix's real AXIUM DX8000 / Move/5000 so we can BUILD and TEST the M2
Worldline adapter with NO hardware and NO real money. When Worldline delivers the real
TIM spec + terminal IP, a real `TerminalLink` (a TCP/TIM client — see
`worldline.TimTcpTerminalLink`) replaces this mock and the adapter ABOVE it does not
change. The visual twin of exactly this flow is
`docs/testing/banco/WORLDLINE-TERMINAL-SIM.html`.

⚠️ PLACEHOLDER PROTOCOL: the message/field shapes here are modelled on the ep2 ECR flow
(OpenReader → RequestPayment → CardPresented → Authorize → Approved). They are a
reasonable stand-in, NOT Worldline's confirmed wire format. When the spec arrives, only
this file + the real `TerminalLink` change — the adapter, checkout, receipts, and tests
stay as-is. Full design: docs/SPEC-payments-seam.md §4.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class TerminalLink(Protocol):
    """Transport to a physical terminal. `MockTerminal` now; a real TCP/TIM client at go-live.

    Three verbs are all the adapter needs: ask the terminal to take a payment, read the
    current result, and abort an in-flight one. Swapping mock → hardware means implementing
    exactly these against the real terminal socket — nothing above this line moves.
    """
    async def request_payment(self, *, amount_minor: int, currency: str, reference: str) -> str: ...
    async def get_result(self, session_id: str) -> dict: ...
    async def abort(self, session_id: str) -> None: ...


# Outcomes the mock can be scripted to produce (so a test can force each branch).
APPROVE = "approve"
DECLINE = "decline"
ABORT = "abort"
TIMEOUT = "timeout"   # the terminal never resolves → the adapter's charge() loop times out


@dataclass
class _Session:
    amount_minor: int
    currency: str
    reference: str
    polls_left: int          # get_result() returns 'pending' this many times before resolving
    aborted: bool = False


@dataclass
class MockTerminal:
    """An in-memory ep2/TIM terminal. Deterministic and scriptable for tests + the sim.

    Fields let a caller model a specific device and a specific outcome:
      name/tid      — which of Felix's terminals this pretends to be (receipt + txn id)
      outcome       — APPROVE | DECLINE | ABORT | TIMEOUT
      method        — card scheme echoed back ('visa'/'mastercard'/'twint') for the receipt
      pending_polls — how many polls return 'pending' before the outcome (models the human
                      tapping their card a beat after the amount appears)
    """
    name: str = "AXIUM DX8000"
    tid: str = "25409030"
    outcome: str = APPROVE
    method: str = "twint"
    pending_polls: int = 0
    _sessions: dict[str, _Session] = field(default_factory=dict, repr=False)
    _session_seq: int = field(default=0, repr=False)
    _txn_seq: int = field(default=0, repr=False)

    async def request_payment(self, *, amount_minor: int, currency: str, reference: str) -> str:
        """POS → terminal: OpenReader + RequestPayment(amount). Returns the session id."""
        if amount_minor <= 0:
            raise ValueError("amount_minor must be a positive integer count of Rappen/cents")
        self._session_seq += 1
        sid = f"{self.tid}-S{self._session_seq:04d}"
        self._sessions[sid] = _Session(amount_minor, currency, reference, self.pending_polls)
        return sid

    async def get_result(self, session_id: str) -> dict:
        """Terminal → POS: the current state of this session."""
        s = self._sessions.get(session_id)
        if s is None:
            return {"status": "error", "reason": "unknown_session"}
        if s.aborted:
            return {"status": "aborted", "reason": "cancelled"}
        if self.outcome == TIMEOUT:
            return {"status": "pending"}          # never resolves on purpose
        if s.polls_left > 0:
            s.polls_left -= 1
            return {"status": "pending"}          # customer hasn't tapped yet
        if self.outcome == DECLINE:
            return {"status": "declined", "reason": "card_refused"}
        if self.outcome == ABORT:
            return {"status": "aborted", "reason": "customer_cancelled"}
        # APPROVE — the money moved; hand back the acquirer's txn id + scheme
        self._txn_seq += 1
        return {
            "status": "approved",
            "txn_id": f"{self.tid}-{self._txn_seq:06d}",
            "scheme": self.method,
            "amount_minor": s.amount_minor,
            "currency": s.currency,
        }

    async def abort(self, session_id: str) -> None:
        """POS → terminal: CancelPayment (cashier hit escape / timed out)."""
        s = self._sessions.get(session_id)
        if s is not None:
            s.aborted = True


# Felix's two real terminals, pre-modelled for the sim + tests (identifiers off the labels,
# docs/testing/banco/field-2026-07-08/BL-19-card-readers.md). "Preferred" = the fixed AXIUM.
def axium_dx8000(**over) -> MockTerminal:
    return MockTerminal(name="AXIUM DX8000", tid="25409030", **over)


def move_5000(**over) -> MockTerminal:
    return MockTerminal(name="Move/5000", tid="25145450", **over)
