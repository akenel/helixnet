"""
The Brain -- Swiss per-line VAT resolver (Banco cafe / head-shop till).

Pure decision logic: given a product's behaviour CLASS and the consumption mode
(dine-in vs takeaway), return the legally-correct VAT rate for that line, and the
VAT contained within a VAT-inclusive price. Encodes FTA MWST Branchen-Info 08
"Gastgewerbe" + Art. 25 MWSTG. Spec: docs/BANCO-CAFE-VAT-SPEC-2026-06-21.md.

The class -> VAT-treatment mapping is NOT duplicated here: it lives in
catalog_taxonomy.PRODUCT_CLASSES[*]["vat"] (the single source of truth -- the same
table that drives the 18+ gate). This module turns a treatment into a Decimal rate
and does the inclusive-VAT math. No DB, no HTTP, no app boot -- so it unit-tests on
the host .venv in milliseconds.

The two facts the law turns on (spec section 2):
  * ALCOHOL and TOBACCO are ALWAYS 8.1% -- their classes are "standard" in the
    taxonomy, so they land standard here no matter the consumption mode.
  * A cafe food/drink line is 8.1% dine-in, 2.6% takeaway -- its class is
    "cafe_split", collapsed below using the consumption mode.

FTA default: an undocumented / unclear sale is PRESUMED standard-rated. So the safe
default is DINE_IN (8.1%); TAKEAWAY (2.6%) must be the deliberate, recorded choice.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from src.services.catalog_taxonomy import class_meta


class Consumption(str, Enum):
    """Where a cafe line is consumed. Drives dine-in vs takeaway VAT."""
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"


# The safe default: undocumented consumption is presumed standard-rated (spec section 2).
DEFAULT_CONSUMPTION = Consumption.DINE_IN


def normalize_consumption(consumption) -> Consumption:
    """Coerce any input to a Consumption; unknown / blank / None -> DINE_IN.

    Defaulting to DINE_IN (not raising) is the legally-conservative choice: a line
    with no recorded takeaway intent is presumed the standard-rated restaurant supply.
    """
    if isinstance(consumption, Consumption):
        return consumption
    try:
        return Consumption(str(consumption).strip().lower())
    except (ValueError, AttributeError):
        return DEFAULT_CONSUMPTION


def vat_treatment(product_class, consumption=DEFAULT_CONSUMPTION) -> str:
    """Resolve a class + consumption mode to a flat treatment: "standard" or "reduced".

    Reads the class's VAT policy from the taxonomy (standard | reduced | cafe_split)
    and collapses "cafe_split" using the consumption mode. Because alcohol and tobacco
    are "standard" in the taxonomy, they always resolve to standard here -- exactly as
    Art. 25 MWSTG requires.
    """
    policy = class_meta(product_class)["vat"]
    if policy == "cafe_split":
        return "reduced" if normalize_consumption(consumption) is Consumption.TAKEAWAY else "standard"
    if policy == "reduced":
        return "reduced"
    return "standard"


def resolve_vat_rate(product_class, consumption=DEFAULT_CONSUMPTION,
                     *, standard_rate=None, reduced_rate=None) -> Decimal:
    """The legally-correct VAT rate (percent Decimal, e.g. Decimal('8.1')) for one line.

    Rates default to config (POS_VAT_RATE / POS_VAT_RATE_REDUCED) but are injectable so
    the rule is testable without booting settings, and so a future rate change (8.1 ->
    8.5 is parliament-proposed) is data, not code.
    """
    std, red = _rates(standard_rate, reduced_rate)
    return red if vat_treatment(product_class, consumption) == "reduced" else std


def contained_vat(gross, rate) -> Decimal:
    """VAT *contained within* a VAT-inclusive gross amount, rounded to cents.

    Swiss retail prices include VAT: for gross G at rate r%, the contained VAT is
    G * r / (100 + r). e.g. 89.90 @ 8.1% -> 6.74. Generalises the single-rate
    pos_router._inclusive_vat to any rate so a cart can mix 8.1% and 2.6% lines.
    """
    g = Decimal(str(gross))
    r = Decimal(str(rate))
    return (g * r / (Decimal("100") + r)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def line_vat(product_class, consumption=DEFAULT_CONSUMPTION, gross=Decimal("0"),
             *, standard_rate=None, reduced_rate=None) -> tuple[Decimal, Decimal]:
    """The (rate, contained-VAT) pair for one sale line — what gets SNAPSHOTTED onto it.

    Resolves the legal rate from the product's class + consumption mode, then computes
    the VAT contained in the line's VAT-inclusive gross. Both numbers are frozen onto the
    line at sale time so a later rate change never rewrites a past receipt. Pure — the
    endpoint just stores what this returns.
    """
    rate = resolve_vat_rate(product_class, consumption,
                            standard_rate=standard_rate, reduced_rate=reduced_rate)
    return rate, contained_vat(gross, rate)


def _rates(standard_rate, reduced_rate) -> tuple[Decimal, Decimal]:
    """(standard, reduced) rates as Decimals. Both injectable; else read from config."""
    if standard_rate is not None and reduced_rate is not None:
        return Decimal(str(standard_rate)), Decimal(str(reduced_rate))
    # Lazy import: only the production path touches settings, so tests that pass explicit
    # rates never need the app config to boot.
    from src.core.config import get_settings
    s = get_settings()
    std = Decimal(str(standard_rate if standard_rate is not None else s.POS_VAT_RATE))
    red = Decimal(str(reduced_rate if reduced_rate is not None else s.POS_VAT_RATE_REDUCED))
    return std, red
