"""Per-supplier trade discount → receiving cost auto-fill (the Ecolution seam).

A supplier can carry a `trade_discount_pct` (% off retail). When set, receiving auto-fills
the cost from the shelf price: cost = retail × (1 − pct/100) — Sylvie prices at her Etsy
RETAIL, Felix pays 70% of it. Money is decided at the cent, so `cost_from_retail` quantizes
HALF-UP to 0.01. These lock the math + the 0-100 schema guard; the UI wiring (auto-fill only
touches a blank/auto cost, never a hand-typed one) is proven by hand on sandbox.
"""
from decimal import Decimal

import pytest

from src.db.models.supplier_model import cost_from_retail
from src.schemas.pos_schema import SupplierCreate, SupplierUpdate


# ---- cost_from_retail: the costing math -------------------------------------
def test_ecolution_case_pays_seventy_percent():
    # Sylvie's CHF 34.59 glasses case, 30% trade discount → Felix pays CHF 24.21.
    assert cost_from_retail(34.59, 30) == Decimal("24.21")


def test_quantizes_half_up_to_the_cent():
    # 19.95 × 0.67 = 13.3665 → rounds up to 13.37 (money is decided at the cent).
    assert cost_from_retail(19.95, 33) == Decimal("13.37")


def test_zero_discount_is_the_retail_price():
    assert cost_from_retail(10, 0) == Decimal("10.00")


def test_full_discount_is_free():
    assert cost_from_retail(42.00, 100) == Decimal("0.00")


def test_result_is_always_two_decimal_places():
    assert str(cost_from_retail(7, 10)) == "6.30"


@pytest.mark.parametrize("retail,pct", [
    (None, 30),        # no price yet → nothing to derive
    (34.59, None),     # no deal → leave the cost blank
    (-1, 30),          # negative price is nonsense
    (10, -5),          # negative discount is nonsense
    (10, 101),         # >100% would pay the customer
])
def test_bad_inputs_return_none_not_a_bogus_cost(retail, pct):
    assert cost_from_retail(retail, pct) is None


# ---- schema guard: 0-100 range ----------------------------------------------
def test_schema_accepts_a_valid_discount():
    s = SupplierCreate(prefix="ECO", name="Ecolution", trade_discount_pct=30)
    assert s.trade_discount_pct == 30


def test_schema_allows_no_deal():
    s = SupplierCreate(prefix="ECO", name="Ecolution")
    assert s.trade_discount_pct is None


@pytest.mark.parametrize("bad", [-1, 100.5, 150])
def test_schema_rejects_out_of_range(bad):
    with pytest.raises(Exception):
        SupplierCreate(prefix="ECO", name="Ecolution", trade_discount_pct=bad)


def test_update_schema_range_guard():
    with pytest.raises(Exception):
        SupplierUpdate(trade_discount_pct=200)
    assert SupplierUpdate(trade_discount_pct=None).trade_discount_pct is None
