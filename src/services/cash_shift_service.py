"""
Cash-shift math -- pure, no DB, no HTTP, so it's trivially unit-testable.

The whole honest loop in three functions:
  expected_cash(...)  -> what SHOULD be in the drawer at close
  close_result(...)   -> variance + within-tolerance verdict
  denoms_total(...)   -> sum a denomination breakdown into a total

Money is Decimal end-to-end, quantized to CHF cents (ROUND_HALF_UP). Only CASH
touches the drawer -- card/twint/debit are reported but never part of the count.
"""
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")

# Swiss franc denominations (notes + coins), in CHF. Used to total a count grid.
# BYTE-IDENTICAL to the original set: keeps the 1000 note + 0.05 coin,
# EXCLUDES 0.01/0.02 (Switzerland has no Rappen below 5). Do NOT reorder/reformat.
CHF_DENOMINATIONS = [
    Decimal("1000"), Decimal("200"), Decimal("100"), Decimal("50"),
    Decimal("20"), Decimal("10"),                       # notes
    Decimal("5"), Decimal("2"), Decimal("1"),
    Decimal("0.50"), Decimal("0.20"), Decimal("0.10"), Decimal("0.05"),  # coins
]

# Euro denominations (notes + coins), in EUR. Includes the 500 note and 1c/2c
# coins -- all legal tender, so all must be countable at closeout or they vanish.
EUR_DENOMINATIONS = [
    Decimal("500"), Decimal("200"), Decimal("100"), Decimal("50"),
    Decimal("20"), Decimal("10"), Decimal("5"),          # notes
    Decimal("2"), Decimal("1"),
    Decimal("0.50"), Decimal("0.20"), Decimal("0.10"),
    Decimal("0.05"), Decimal("0.02"), Decimal("0.01"),   # coins
]

# US dollar denominations (notes + coins), in USD.
USD_DENOMINATIONS = [
    Decimal("100"), Decimal("50"), Decimal("20"), Decimal("10"),
    Decimal("5"), Decimal("1"),                          # notes
    Decimal("0.25"), Decimal("0.10"), Decimal("0.05"), Decimal("0.01"),  # coins
]

_DENOMS_BY_CURRENCY = {
    "CHF": CHF_DENOMINATIONS,
    "EUR": EUR_DENOMINATIONS,
    "USD": USD_DENOMINATIONS,
}


def denoms_for(currency="CHF"):
    """Ordered face-value list for a currency (falls back to CHF for unknowns)."""
    return _DENOMS_BY_CURRENCY.get((currency or "CHF").upper(), CHF_DENOMINATIONS)


# Back-compat: the CHF whitelist, for anything that imported it directly.
_VALID_DENOMS = {str(d) for d in CHF_DENOMINATIONS}


def _d(v) -> Decimal:
    """Coerce anything moneyish to a Decimal; None/'' -> 0."""
    if v is None or v == "":
        return Decimal("0")
    return v if isinstance(v, Decimal) else Decimal(str(v))


def money(v) -> Decimal:
    """Quantize to CHF cents, half-up."""
    return _d(v).quantize(CENTS, rounding=ROUND_HALF_UP)


def expected_cash(opening_float, cash_sales, paid_in, paid_out, cash_refunds) -> Decimal:
    """What should physically be in the drawer at close.

    float you started with
      + cash you took from sales
      + cash brought in (float top-ups)
      - cash taken out (petty cash)
      - cash you refunded to customers
    """
    total = (_d(opening_float) + _d(cash_sales) + _d(paid_in)
             - _d(paid_out) - _d(cash_refunds))
    return money(total)


def close_result(expected, counted, tolerance=Decimal("0.20")) -> dict:
    """Compare the counted drawer to expectation.

    variance = counted - expected   (negative = short, positive = over)
    within   = abs(variance) <= tolerance
    """
    exp = money(expected)
    cnt = money(counted)
    tol = money(tolerance)
    variance = money(cnt - exp)
    return {
        "expected": exp,
        "counted": cnt,
        "variance": variance,
        "tolerance": tol,
        "within_tolerance": abs(variance) <= tol,
        "short": variance < 0,
    }


def denoms_total(denoms, currency="CHF") -> Decimal:
    """Sum a {denomination: count} map into a total in the given currency.

    Keys are face values as strings ("50", "0.05"); values are counts. Validation
    is against the CURRENCY-APPROPRIATE denomination set -- a EUR 500 note or a
    1c/2c coin is valid under EUR but not under CHF. Unknown denominations and junk
    counts are ignored (robust to a noisy client). Default currency is CHF so every
    pre-existing call site keeps byte-identical behavior.
    """
    if not isinstance(denoms, dict):
        return Decimal("0")
    valid = {str(d) for d in denoms_for(currency)}
    total = Decimal("0")
    for face, count in denoms.items():
        if str(face) not in valid:
            continue
        try:
            n = int(count)
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        total += Decimal(str(face)) * n
    return money(total)
