"""
The Brain -- truth-table tests for the Swiss per-line VAT resolver.

Pure unit tests. No DB, no HTTP, no settings boot -- every test passes explicit
rates, so these run on the host .venv in milliseconds (like test_cash_math).

LOCKS the legal rule (spec docs/BANCO-CAFE-VAT-SPEC-2026-06-21.md, section 2):
  * alcohol + tobacco are ALWAYS 8.1%, regardless of dine-in/takeaway
  * cafe food/drink: 8.1% dine-in, 2.6% takeaway
  * retail / CBD / unknown: 8.1%
  * undocumented consumption is PRESUMED standard (default DINE_IN -> 8.1%)
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Import the service directly (no app, no fastapi).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.vat_resolver import (  # noqa: E402
    Consumption, DEFAULT_CONSUMPTION,
    normalize_consumption, vat_treatment, resolve_vat_rate, contained_vat,
)

STD = Decimal("8.1")   # standard rate
RED = Decimal("2.6")   # reduced rate (takeaway food / non-alc drink)


def rate(product_class, consumption=DEFAULT_CONSUMPTION):
    """resolve_vat_rate with the in-force rates injected -- keeps the test pure."""
    return resolve_vat_rate(product_class, consumption, standard_rate=STD, reduced_rate=RED)


# --- THE TRUTH TABLE (spec section 2) ----------------------------------------

@pytest.mark.parametrize("product_class, consumption, expected", [
    # Retail head-shop goods -- always standard, even if someone marks takeaway.
    ("standard",         Consumption.DINE_IN,  STD),
    ("standard",         Consumption.TAKEAWAY, STD),
    # Tobacco / nicotine -- ALWAYS 8.1% (Art. 25 MWSTG), both modes.
    ("tobacco_nicotine", Consumption.DINE_IN,  STD),
    ("tobacco_nicotine", Consumption.TAKEAWAY, STD),
    # Alcohol -- ALWAYS 8.1%, both modes (a beer in the cafe is still standard).
    ("alcohol",          Consumption.DINE_IN,  STD),
    ("alcohol",          Consumption.TAKEAWAY, STD),
    # CBD / Hemp (18+ and open forms) -- retail goods, standard.
    ("cbd_hemp",         Consumption.TAKEAWAY, STD),
    ("cbd_open",         Consumption.TAKEAWAY, STD),
    # Cafe food/drink -- THE SPLIT. 8.1% on-site, 2.6% to-go.
    ("cafe_food",        Consumption.DINE_IN,  STD),
    ("cafe_food",        Consumption.TAKEAWAY, RED),
])
def test_truth_table(product_class, consumption, expected):
    assert rate(product_class, consumption) == expected


# --- THE DEFAULT IS LEGALLY CONSERVATIVE -------------------------------------

def test_cafe_food_default_is_dine_in_standard():
    # No consumption given -> presumed standard-rated (the safe default).
    assert rate("cafe_food") == STD
    assert DEFAULT_CONSUMPTION is Consumption.DINE_IN


def test_unknown_consumption_falls_back_to_standard():
    # Garbage / blank consumption must never accidentally grant the cheaper rate.
    for bad in ("garbage", "", None, "DINE", 0):
        assert rate("cafe_food", bad) == STD


def test_unknown_or_missing_class_is_standard():
    # Unknown / None class -> taxonomy default ("standard") -> 8.1%.
    assert rate(None) == STD
    assert rate("not_a_real_class") == STD


# --- THE MONEY DIFFERENCE IS REAL --------------------------------------------

def test_takeaway_is_cheaper_for_cafe_food_only():
    assert rate("cafe_food", Consumption.TAKEAWAY) < rate("cafe_food", Consumption.DINE_IN)
    # ...but takeaway does NOT discount alcohol/tobacco/retail.
    assert rate("alcohol", Consumption.TAKEAWAY) == rate("alcohol", Consumption.DINE_IN)
    assert rate("standard", Consumption.TAKEAWAY) == rate("standard", Consumption.DINE_IN)


# --- RATES ARE DATA, NOT HARDCODED (spec section 1) --------------------------

def test_rates_are_injectable():
    # A standard-rate rise (8.1 -> 8.5 is parliament-proposed) is a config change.
    assert resolve_vat_rate("standard", standard_rate="8.5", reduced_rate="2.6") == Decimal("8.5")
    assert resolve_vat_rate("cafe_food", Consumption.TAKEAWAY,
                            standard_rate="8.5", reduced_rate="2.6") == Decimal("2.6")


# --- normalize_consumption + vat_treatment seams -----------------------------

def test_normalize_consumption():
    assert normalize_consumption("takeaway") is Consumption.TAKEAWAY
    assert normalize_consumption("DINE_IN".lower()) is Consumption.DINE_IN
    assert normalize_consumption(Consumption.TAKEAWAY) is Consumption.TAKEAWAY
    assert normalize_consumption(" Takeaway ") is Consumption.TAKEAWAY  # trims + lowercases
    assert normalize_consumption(None) is DEFAULT_CONSUMPTION
    assert normalize_consumption("nonsense") is DEFAULT_CONSUMPTION


def test_vat_treatment_collapses_to_two_buckets():
    assert vat_treatment("cafe_food", Consumption.TAKEAWAY) == "reduced"
    assert vat_treatment("cafe_food", Consumption.DINE_IN) == "standard"
    assert vat_treatment("alcohol", Consumption.TAKEAWAY) == "standard"
    assert vat_treatment("standard") == "standard"


# --- INCLUSIVE VAT MATH (the contained-VAT helper) ---------------------------

def test_contained_vat_standard_rate():
    # Spec worked example: CHF 89.90 @ 8.1% -> 6.74 contained VAT.
    assert contained_vat("89.90", STD) == Decimal("6.74")


def test_contained_vat_reduced_rate():
    # A CHF 5.00 takeaway coffee @ 2.6% -> 0.13 contained VAT.
    assert contained_vat("5.00", RED) == Decimal("0.13")


def test_contained_vat_exact_boundary():
    # Gross == 100 + rate -> contained VAT == rate exactly (108.10 @ 8.1% -> 8.10).
    assert contained_vat("108.10", STD) == Decimal("8.10")


def test_contained_vat_rounds_half_up_to_cents():
    assert contained_vat("89.90", STD).as_tuple().exponent == -2  # always 2 dp
    assert contained_vat(10, "2.6") == Decimal("0.25")  # 10*2.6/102.6 = 0.2534 -> 0.25
