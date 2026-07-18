"""Flat plan-rate currency conversion (Angel's design — deliberately coarse).

No live FX feed and no per-second drift: a small hand-set rate table (a "plan rate" you
update monthly or yearly) turns a foreign supplier price into the shop's own currency for
DISPLAY + price comparison. "Whatever it is, it is." Missing a rate → don't guess, just show
the foreign price as-is.

Rates are stored per-tenant on ``store_settings.fx_rates`` (JSON) and fall back to
``DEFAULT_FX``. A rate is "how many BASE units per 1 unit of the foreign currency" — so
``base_amount = foreign_amount * rate``.
"""
from __future__ import annotations

import json
import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

log = logging.getLogger("currency")

# Plan rates → base units per 1 foreign unit. Base = CHF (the Artemis shop). Update on review.
DEFAULT_FX = {
    "base": "CHF",
    "as_of": "2026-07 (plan)",
    "rates": {"EUR": 0.96, "USD": 0.88, "GBP": 1.11, "CNY": 0.12, "PLN": 0.22},
}


def load_fx(fx_rates_json: str | None) -> dict:
    """Parse the tenant's ``store_settings.fx_rates`` JSON, else the built-in default."""
    if fx_rates_json:
        try:
            fx = json.loads(fx_rates_json)
            if isinstance(fx, dict) and isinstance(fx.get("rates"), dict):
                fx.setdefault("base", DEFAULT_FX["base"])
                fx.setdefault("as_of", "custom")
                return fx
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            log.warning("bad fx_rates JSON, using default: %s", e)
    return DEFAULT_FX


def convert(amount, from_ccy: str, base_ccy: str = "CHF", fx: dict | None = None) -> dict | None:
    """Convert ``amount`` ``from_ccy`` → the shop base. Returns
    ``{base_amount, base_ccy, rate, as_of}`` or None (same currency / no rate / bad amount)."""
    if amount is None:
        return None
    from_ccy = (from_ccy or "").upper().strip()
    base_ccy = (base_ccy or "CHF").upper().strip()
    if not from_ccy or from_ccy == base_ccy:
        return None
    fx = fx or DEFAULT_FX
    rate = (fx.get("rates") or {}).get(from_ccy)
    if rate is None:
        return None
    try:
        base_amt = (Decimal(str(amount)) * Decimal(str(rate))).quantize(Decimal("0.01"), ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return None
    return {"base_amount": float(base_amt), "base_ccy": base_ccy,
            "rate": float(rate), "as_of": fx.get("as_of")}


def to_tender(base_amount, to_ccy: str, base_ccy: str = "CHF", fx: dict | None = None) -> dict | None:
    """A HOME/base amount → the foreign TENDER equivalent (what to collect if the customer pays in
    ``to_ccy``). The inverse of ``convert``: ``tender = base / rate`` (rate = base units per 1 foreign).
    Returns ``{tender_amount, to_ccy, rate, as_of}`` or None (same currency / no rate / bad amount)."""
    if base_amount is None:
        return None
    to_ccy = (to_ccy or "").upper().strip()
    base_ccy = (base_ccy or "CHF").upper().strip()
    if not to_ccy or to_ccy == base_ccy:
        return None
    fx = fx or DEFAULT_FX
    rate = (fx.get("rates") or {}).get(to_ccy)
    if rate in (None, 0):
        return None
    try:
        amt = (Decimal(str(base_amount)) / Decimal(str(rate))).quantize(Decimal("0.01"), ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
        return None
    return {"tender_amount": float(amt), "to_ccy": to_ccy, "rate": float(rate), "as_of": fx.get("as_of")}

