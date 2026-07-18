# File: src/payments/resolver.py
"""
Provider resolution + the checkout hook.

`payment_provider` is a per-store setting (store_settings.payment_provider); the default
'manual' means "no electronic terminal — the cashier takes payment by hand", which is
today's behaviour with ZERO change.

Adapters register in _ADAPTERS as they ship. It is EMPTY in M1, so get_payment_provider
always returns None and capture_on_terminal_if_configured is a proven no-op in every
current env. M2 registers 'worldline' → the seam lights up with no change to the callers.
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.store_settings_model import StoreSettingsModel
from .base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)

# name -> async factory(db) -> PaymentProvider. Populated as adapters land (M2: worldline).
_ADAPTERS: dict[str, Callable[[AsyncSession], Awaitable[PaymentProvider]]] = {}

# Values that mean "no terminal to drive" → resolver returns None → no regression.
_MANUAL = {"", "manual", "none", "cash"}


async def _store_payment_provider(db: AsyncSession) -> str:
    """The electronic payment provider THIS shop is wired to (default 'manual').

    Mirrors _store_currency: read it off the store row, never assume. A store with no row,
    a NULL column, or an env that predates the column all resolve to 'manual'.
    """
    try:
        store = (await db.execute(
            select(StoreSettingsModel).order_by(StoreSettingsModel.store_number))).scalars().first()
        return (getattr(store, "payment_provider", None) or "manual").strip().lower()
    except Exception:
        return "manual"


async def get_payment_provider(db: AsyncSession) -> Optional[PaymentProvider]:
    """The terminal adapter for this store, or None when there's nothing to drive.

    None ⇒ the sale completes exactly as today (cash / card / TWINT confirmed by hand).
    """
    name = await _store_payment_provider(db)
    if name in _MANUAL:
        return None
    factory = _ADAPTERS.get(name)
    if factory is None:
        # A provider is named but no adapter is built yet (e.g. pre-M2 'worldline'). Fail
        # SAFE to manual so a mis-set value can never break the till (prove-don't-assume).
        logger.warning("store payment_provider=%r has no adapter yet — treating as manual", name)
        return None
    return await factory(db)


async def capture_on_terminal_if_configured(
    db: AsyncSession, transaction
) -> Optional[PaymentResult]:
    """Seam hook wired into BOTH sale-completion paths (checkout_transaction + create_sale).

    Returns None when the store has no electronic terminal provider — the default — so the
    sale completes byte-identically to today. When a provider IS configured (M2: Worldline
    TIM), this will drive the terminal, record a PaymentModel row, and return the
    PaymentResult for the caller to gate completion on.
    """
    provider = await get_payment_provider(db)
    if provider is None:
        return None
    # Real capture (build intent → initiate → await approved → persist PaymentModel) lands in
    # M2 with the Worldline adapter, when there's a terminal to prove it against.
    raise NotImplementedError(
        f"terminal capture for provider {provider.name!r} is not built yet (M2)")
