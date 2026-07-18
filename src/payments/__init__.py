# File: src/payments/__init__.py
"""🌍-1 payments seam — provider-agnostic terminal capture (Worldline TIM first).

See docs/SPEC-payments-seam.md and memory `banco-payments-provider-seam`.
"""
from .base import (
    PaymentIntent,
    PaymentProvider,
    PaymentResult,
    PaymentStatus,
    to_minor_units,
)
from .resolver import (
    _store_payment_provider,
    capture_on_terminal_if_configured,
    get_payment_provider,
)
from .mock_terminal import MockTerminal, TerminalLink, axium_dx8000, move_5000
from .worldline import TimTcpTerminalLink, WorldlineTIMAdapter

__all__ = [
    "PaymentIntent",
    "PaymentProvider",
    "PaymentResult",
    "PaymentStatus",
    "to_minor_units",
    "get_payment_provider",
    "capture_on_terminal_if_configured",
    "_store_payment_provider",
    # M2 — Worldline TIM adapter + the mock terminal it's built against
    "WorldlineTIMAdapter",
    "TimTcpTerminalLink",
    "TerminalLink",
    "MockTerminal",
    "axium_dx8000",
    "move_5000",
]
