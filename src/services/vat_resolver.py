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


# --- N-RATE TABLE (P3, docs/BANCO-GO-ITALIAN-PLAN.md) ----------------------------------------
# A rate table is an ORDERED list of streams: [{"code","label","rate"}]. The FIRST entry (or one
# flagged "default": True) is the DEFAULT / standard / CATCH-ALL code: any line whose snapshotted
# rate matches NO configured code buckets HERE — it is NEVER dropped (CRIT #1: total coverage; a
# legacy 7.7% / 0% / null line must still land in the Z-report). For CH the table is exactly
# [{A/standard, 8.1}, {B/reduced, 2.6}] built FROM CONFIG (POS_VAT_RATE / _REDUCED) so the Swiss
# rates keep their single source of truth. A jurisdiction with N rates (IT: 22/10/5/4) just passes
# a longer table — the math below is rate-count-agnostic.
CH_STANDARD_CODE = "A"   # standard / default / catch-all
CH_REDUCED_CODE = "B"    # reduced (takeaway cafe food/drink)


def ch_rate_table(standard_rate=None, reduced_rate=None) -> list[dict]:
    """The Swiss two-rate table, built from config (or injected rates). The ONE place the CH
    default table is defined — callers that pass no `rate_table` to split_vat get exactly this."""
    std, red = _rates(standard_rate, reduced_rate)
    return [
        {"code": CH_STANDARD_CODE, "label": "standard", "rate": std, "default": True},
        {"code": CH_REDUCED_CODE, "label": "reduced", "rate": red},
    ]


def _normalize_rate_table(rate_table) -> list[dict]:
    """Coerce a caller's rate table to canonical shape (rate → Decimal, label/default present)."""
    out = []
    for e in rate_table:
        out.append({
            "code": e["code"],
            "label": e.get("label", e["code"]),
            "rate": Decimal(str(e["rate"])),
            "default": bool(e.get("default", False)),
        })
    return out


def split_vat(lines, total, subtotal, *, standard_rate=None, reduced_rate=None,
              rate_table=None) -> dict:
    """Roll a sale's lines up into the jurisdiction's N turnover streams (INC3, N-rate).

    `lines` = iterable of (rate, line_total) — the per-line snapshotted VAT rate and its
    GROSS (pre-discount). `total`/`subtotal` = the sale's discounted gross and pre-discount
    subtotal; their ratio prorates a cart-wide discount evenly across lines so each line's
    contained VAT reflects what was actually charged.

    `rate_table` (P3) = ordered [{code,label,rate}]; the first / "default"-flagged entry is the
    CATCH-ALL. Omitted → the CH two-rate table from config, so every legacy caller (and the CH
    golden lock) is byte-identical to the previous two-stream behaviour.

    Returns:
      * `vat_streams`: {code: {code,label,rate,turnover,vat}} — the N streams (the new truth).
      * back-compat scalars `turnover_standard/reduced`, `vat_standard/reduced`, `vat_total` —
        standard = the DEFAULT code's stream; reduced = the SUM of every non-default stream, so
        `vat_total == vat_standard + vat_reduced` still holds and CH (one non-default code) is
        numerically identical to before. Pure + cents-rounded.

    TOTAL COVERAGE (CRIT #1): a line whose rate matches no code buckets to the default code —
    never dropped. A naive dict keyed only by the configured rates would silently lose a 7.7% /
    0% / null line and under-report the Z-report; this preserves the old `else → standard` reach.
    """
    if rate_table is None:
        rate_table = ch_rate_table(standard_rate, reduced_rate)
    table = _normalize_rate_table(rate_table)
    if not table:  # defensive: an empty table degrades to CH, never a crash / silent drop
        table = _normalize_rate_table(ch_rate_table(standard_rate, reduced_rate))

    default_code = next((e["code"] for e in table if e["default"]), table[0]["code"])
    default_rate = next(e["rate"] for e in table if e["code"] == default_code)
    rate_to_code: dict = {}
    for e in table:
        rate_to_code.setdefault(e["rate"], e["code"])  # first wins on a duplicate rate

    sub = Decimal(str(subtotal or 0))
    factor = (Decimal(str(total)) / sub) if sub > 0 else Decimal("1")
    streams = {e["code"]: {"code": e["code"], "label": e["label"], "rate": e["rate"],
                           "turnover": Decimal("0"), "vat": Decimal("0")} for e in table}
    for rate, line_total in lines:
        r = Decimal(str(rate)) if rate is not None else default_rate
        gross = Decimal(str(line_total or 0)) * factor
        vat = contained_vat(gross, r)
        code = rate_to_code.get(r, default_code)  # unmatched rate → default (TOTAL COVERAGE)
        streams[code]["turnover"] += gross
        streams[code]["vat"] += vat

    cents = lambda d: d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    for s in streams.values():
        s["turnover"] = cents(s["turnover"])
        s["vat"] = cents(s["vat"])

    dflt = streams[default_code]
    non_default = [s for c, s in streams.items() if c != default_code]
    o = {
        "vat_streams": streams,
        "turnover_standard": dflt["turnover"],
        "vat_standard": dflt["vat"],
        "turnover_reduced": cents(sum((s["turnover"] for s in non_default), Decimal("0"))),
        "vat_reduced": cents(sum((s["vat"] for s in non_default), Decimal("0"))),
    }
    o["vat_total"] = o["vat_standard"] + o["vat_reduced"]
    return o


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
