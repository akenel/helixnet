"""BL-26 quantity-break (tier) pricing.

A product may carry ``price_tiers`` = ``[{"min_qty": int, "unit_price": "4.90"}, ...]``.
When a cart line's quantity reaches a tier's ``min_qty``, that tier's unit price applies
to the WHOLE line. It is a PRICE (feeds VAT + totals), not a discount.

Per Angel's decision (2026-07-11), a line that got a *volume* break (``min_qty >= 2``) is
FINAL — no further member/manual discount stacks on it. ``tier_unit_price`` returns that
flag so the checkout can exclude the line from the discount base.

unit_price is stored as a STRING in JSON (e.g. "4.90") to keep money exact through the
JSON round-trip; everything quantizes to cents on read.
"""
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def _q(v) -> Decimal:
    """Quantize any numeric-ish value to cents (money-safe compare/serialize)."""
    return Decimal(str(v)).quantize(_CENT, rounding=ROUND_HALF_UP)


def tier_unit_price(price_tiers, base_price, qty, mode="per_unit"):
    """Resolve the effective UNIT price for ``qty`` from ``price_tiers``.

    Returns ``(unit_price: Decimal, volume_break: bool)``. The winning tier is the one with
    the highest ``min_qty`` still ``<= qty``. ``mode`` decides what a tier's stored value means:
      - ``"per_unit"`` (default, Artemis style): the value is the price EACH at ``qty >= min_qty``.
      - ``"bundle"`` ("N for X"): the value is the TOTAL for a pack of ``min_qty``; the per-unit
        rate is ``X / min_qty``, returned FULL-PRECISION so the line total is exact at the pack
        size (the caller quantizes the LINE — see ``tier_line_total``). "3 for 4.00" -> 1.3333…/u
        -> at qty 3 the line is exactly 4.00.
    ``volume_break`` is True only for a genuine break (``min_qty >= 2``) — flags the line
    discount-final. Falls back to ``base_price`` when there are no tiers or none apply.
    """
    base = _q(base_price)
    if not price_tiers:
        return base, False
    best_qty = None
    best_up = None
    for t in price_tiers:
        try:
            mq = int(t.get("min_qty"))
            up = t.get("unit_price")
        except (TypeError, ValueError, AttributeError):
            continue
        if up is None or mq < 1 or qty < mq:
            continue
        if best_qty is None or mq > best_qty:
            best_qty, best_up = mq, up
    if best_qty is None:
        return base, False
    if mode == "bundle":
        eff = Decimal(str(best_up)) / Decimal(best_qty)   # pack total / pack size, full precision
    else:
        eff = _q(best_up)
    return eff, best_qty >= 2


def tier_line_total(price_tiers, base_price, qty, mode="per_unit"):
    """The quantized LINE total for ``qty`` (effective unit × qty, rounded to cents).

    Line-level rounding is what makes bundle exact: "3 for 4.00" → unit 1.3333… → 1.3333…×3
    quantizes to 4.00. Used by the till AND the client cart-preview so shown == charged."""
    unit, _ = tier_unit_price(price_tiers, base_price, qty, mode)
    return (unit * Decimal(qty)).quantize(_CENT, rounding=ROUND_HALF_UP)


def validate_price_tiers(raw):
    """Validate + normalize a tier list for storage (the editor path).

    Rules: each row is ``{min_qty (int >= 1), unit_price (>= 0)}``; ``min_qty`` values are
    unique; the list is returned sorted ascending; the first tier must be ``min_qty == 1``
    (the base price). ``None``/empty -> ``[]`` (tiers cleared, flat price). Raises
    ``ValueError`` on bad input so the caller can 422 with the reason.
    """
    if not raw:
        return []
    rows = []
    seen = set()
    for t in raw:
        if not isinstance(t, dict):
            raise ValueError("each tier must be an object")
        try:
            mq = int(t["min_qty"])
            up = _q(t["unit_price"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("each tier needs a whole min_qty and a numeric unit_price")
        if mq < 1:
            raise ValueError("min_qty must be >= 1")
        if up < 0:
            raise ValueError("unit_price must be >= 0")
        if mq in seen:
            raise ValueError(f"duplicate min_qty {mq}")
        seen.add(mq)
        rows.append({"min_qty": mq, "unit_price": str(up)})
    rows.sort(key=lambda r: r["min_qty"])
    if rows[0]["min_qty"] != 1:
        raise ValueError("the first tier must start at min_qty 1 (the base price)")
    return rows
