"""BL-26 tier pricing — unit tests for the break-selection + validation helpers."""
from decimal import Decimal

import pytest

from src.services.pricing import tier_unit_price, validate_price_tiers

# The real GIZEH tubes ladder from artemisluzern.ch.
GIZEH = [
    {"min_qty": 1, "unit_price": "4.90"},
    {"min_qty": 10, "unit_price": "4.50"},
    {"min_qty": 50, "unit_price": "4.30"},
    {"min_qty": 100, "unit_price": "3.90"},
]


@pytest.mark.parametrize("qty,price,brk", [
    (1, "4.90", False),    # base tier — not a volume break
    (5, "4.90", False),    # still base, below the 10 break
    (9, "4.90", False),
    (10, "4.50", True),    # first real break
    (49, "4.50", True),
    (50, "4.30", True),
    (99, "4.30", True),
    (100, "3.90", True),
    (500, "3.90", True),   # above the top tier → top price holds
])
def test_gizeh_ladder(qty, price, brk):
    up, volume_break = tier_unit_price(GIZEH, Decimal("4.90"), qty)
    assert up == Decimal(price)
    assert volume_break is brk


def test_no_tiers_falls_back_to_base():
    assert tier_unit_price(None, Decimal("2.50"), 100) == (Decimal("2.50"), False)
    assert tier_unit_price([], Decimal("2.50"), 100) == (Decimal("2.50"), False)


def test_base_price_quantized():
    up, brk = tier_unit_price([], Decimal("2.5"), 1)
    assert up == Decimal("2.50")


def test_malformed_tiers_ignored_not_crash():
    bad = [{"min_qty": None, "unit_price": "1.00"}, {"min_qty": 10}, {"nope": 1}]
    up, brk = tier_unit_price(bad, Decimal("4.90"), 20)
    assert up == Decimal("4.90") and brk is False


def test_validate_normalizes_and_sorts():
    out = validate_price_tiers([
        {"min_qty": 100, "unit_price": "3.9"},
        {"min_qty": 1, "unit_price": 4.9},
        {"min_qty": 10, "unit_price": "4.50"},
    ])
    assert [r["min_qty"] for r in out] == [1, 10, 100]
    assert out[0]["unit_price"] == "4.90"      # quantized to cents, stored as string
    assert out[2]["unit_price"] == "3.90"


def test_validate_empty_clears():
    assert validate_price_tiers(None) == []
    assert validate_price_tiers([]) == []


def test_validate_requires_first_tier_min_qty_1():
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 10, "unit_price": "4.50"}])


def test_validate_rejects_duplicate_and_negative():
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 1, "unit_price": "1.00"}, {"min_qty": 1, "unit_price": "2.00"}])
    with pytest.raises(ValueError):
        validate_price_tiers([{"min_qty": 1, "unit_price": "-1.00"}])
