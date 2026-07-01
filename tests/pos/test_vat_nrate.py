"""N-RATE VAT engine — reconciliation + total-coverage tests (P3 of BANCO-GO-ITALIAN-PLAN.md).

Pure host unit tests (no DB / HTTP / settings boot — explicit rates & rate tables injected),
like test_vat_resolver / test_cash_math.

Proves the generalised `split_vat`:
  * returns N `vat_streams` keyed by rate code, cent-exact;
  * keeps the CH back-compat scalars (turnover_standard/reduced, vat_standard/reduced, vat_total);
  * RECONCILES: Σ stream turnover == subtotal, Σ stream vat == vat_total, cent-exact;
  * is TOTAL-COVERAGE (CRIT #1): a line whose rate matches NO configured code is bucketed to the
    DEFAULT/standard code — never dropped (else the Z-report under-reports).

HONESTY: green here proves the engine is ARITHMETICALLY correct and jurisdiction-agnostic — NOT
that any Italian rate assignment is legally valid. IT class→rate (22/10/5/4) is TBD-by-commercialista
(see fiscal_regime.IT_RATE_TABLE_TBD) and is intentionally NOT asserted as law here.
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.vat_resolver import (  # noqa: E402
    split_vat, ch_rate_table, CH_STANDARD_CODE, CH_REDUCED_CODE,
)


def _D(s):
    return Decimal(str(s))


def _cents(d):
    return _D(d).quantize(Decimal("0.01"))


# A synthetic 4-rate table (shape only — NOT a claim about which Italian goods are 22/10/5/4).
IT_SHAPE_TABLE = [
    {"code": "22", "label": "ordinaria", "rate": "22", "default": True},
    {"code": "10", "label": "ridotta",   "rate": "10"},
    {"code": "5",  "label": "ridotta5",  "rate": "5"},
    {"code": "4",  "label": "minima",    "rate": "4"},
]


# --- CH default table: byte-identical to the legacy two-stream behaviour ----------------------

def test_ch_default_table_reconciles():
    # Injected CH rates, no rate_table → the ch_rate_table default.
    lines = [("8.1", "108.10"), ("2.6", "51.30"), ("8.1", "10.81")]
    subtotal = "170.21"
    s = split_vat(lines, subtotal, subtotal, standard_rate="8.1", reduced_rate="2.6")
    # streams keyed by CH codes
    assert set(s["vat_streams"].keys()) == {CH_STANDARD_CODE, CH_REDUCED_CODE}
    # Σ stream turnover == subtotal, Σ stream vat == vat_total
    tt = sum(st["turnover"] for st in s["vat_streams"].values())
    tv = sum(st["vat"] for st in s["vat_streams"].values())
    assert tt == _D(subtotal)
    assert tv == s["vat_total"]
    # back-compat scalars still present + consistent
    assert s["vat_total"] == s["vat_standard"] + s["vat_reduced"]
    assert s["turnover_standard"] == s["vat_streams"][CH_STANDARD_CODE]["turnover"]
    assert s["turnover_reduced"] == s["vat_streams"][CH_REDUCED_CODE]["turnover"]


# --- CRIT #1: TOTAL COVERAGE — a no-match rate falls to default, never dropped ----------------

def test_unmatched_rate_falls_to_default_not_dropped():
    # 7.7% (historical) + 0% (giveaway) + a null-rate line: none is the reduced 2.6% code, and
    # 7.7/0/null are not the standard 8.1% code either — all MUST bucket to the default (A).
    lines = [
        ("8.1", "108.10"),   # standard
        ("2.6", "51.30"),    # reduced
        ("7.7", "107.70"),   # legacy — matches no configured code → default
        ("0",   "40.00"),    # zero-rated giveaway-priced — matches no code → default
        (None,  "10.00"),    # null rate → default rate → default code
    ]
    subtotal = "317.10"
    s = split_vat(lines, subtotal, subtotal, standard_rate="8.1", reduced_rate="2.6")
    # NOTHING dropped: every franc of turnover is accounted for.
    tt = sum(st["turnover"] for st in s["vat_streams"].values())
    assert tt == _D(subtotal), "turnover leaked — a no-match line was dropped"
    # The unmatched lines all live in the default/standard stream.
    assert s["vat_streams"][CH_STANDARD_CODE]["turnover"] == _cents(
        _D("108.10") + _D("107.70") + _D("40.00") + _D("10.00")
    )
    assert s["vat_streams"][CH_REDUCED_CODE]["turnover"] == _D("51.30")
    # vat reconciles cent-exact.
    tv = sum(st["vat"] for st in s["vat_streams"].values())
    assert tv == s["vat_total"] == s["vat_standard"] + s["vat_reduced"]


# --- N-rate (4 codes) reconciliation — engine is rate-count-agnostic (shape, not IT law) ------

def test_four_rate_table_reconciles_cent_exact():
    lines = [
        ("22", "122.00"),   # ordinaria
        ("10", "110.00"),   # ridotta
        ("5",  "105.00"),   # ridotta 5
        ("4",  "104.00"),   # minima
        ("13", "50.00"),    # NO matching code → default (22)
        (None, "22.00"),    # null → default rate → default code
    ]
    subtotal = "513.00"
    s = split_vat(lines, subtotal, subtotal, rate_table=IT_SHAPE_TABLE)
    assert set(s["vat_streams"].keys()) == {"22", "10", "5", "4"}
    # Σ turnover == subtotal (nothing dropped — 13% + null landed on default).
    tt = sum(st["turnover"] for st in s["vat_streams"].values())
    assert tt == _D(subtotal)
    # Σ vat == vat_total, cent-exact.
    tv = sum(st["vat"] for st in s["vat_streams"].values())
    assert tv == s["vat_total"]
    # default stream carried its own line + the two unmatched lines.
    assert s["vat_streams"]["22"]["turnover"] == _cents(_D("122.00") + _D("50.00") + _D("22.00"))
    # back-compat: standard = default (22); reduced = SUM of the other three streams.
    assert s["vat_standard"] == s["vat_streams"]["22"]["vat"]
    assert s["vat_reduced"] == _cents(
        s["vat_streams"]["10"]["vat"] + s["vat_streams"]["5"]["vat"] + s["vat_streams"]["4"]["vat"]
    )


def test_discount_prorates_across_streams():
    # 10% off a 2-stream cart: each stream's turnover scales by 0.9, vat_total reconciles.
    lines = [("8.1", "100.00"), ("2.6", "100.00")]
    s = split_vat(lines, "180.00", "200.00", standard_rate="8.1", reduced_rate="2.6")
    assert s["vat_streams"][CH_STANDARD_CODE]["turnover"] == _D("90.00")
    assert s["vat_streams"][CH_REDUCED_CODE]["turnover"] == _D("90.00")
    tt = sum(st["turnover"] for st in s["vat_streams"].values())
    assert tt == _D("180.00")
    assert sum(st["vat"] for st in s["vat_streams"].values()) == s["vat_total"]


def test_empty_table_degrades_to_ch_never_crashes():
    lines = [("8.1", "108.10")]
    s = split_vat(lines, "108.10", "108.10", standard_rate="8.1", reduced_rate="2.6",
                  rate_table=[])
    assert set(s["vat_streams"].keys()) == {CH_STANDARD_CODE, CH_REDUCED_CODE}
    assert s["vat_streams"][CH_STANDARD_CODE]["turnover"] == _D("108.10")


def test_ch_rate_table_shape():
    t = ch_rate_table("8.1", "2.6")
    assert [e["code"] for e in t] == [CH_STANDARD_CODE, CH_REDUCED_CODE]
    assert t[0]["default"] is True and t[0]["rate"] == Decimal("8.1")
    assert t[1]["rate"] == Decimal("2.6")
