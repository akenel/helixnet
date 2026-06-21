"""
Pure unit tests for the cash-shift math. No DB, no HTTP -- imports the service
directly, so these run on the host .venv in milliseconds.

LOCKS the drawer accounting: expected = float + cash sales + paid-in - paid-out
- refunds; variance = counted - expected; within = |variance| <= tolerance (0.20).
"""
import sys
from decimal import Decimal
from pathlib import Path

# Import the service directly (no app, no fastapi).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.cash_shift_service import (  # noqa: E402
    expected_cash, close_result, denoms_total, money, CHF_DENOMINATIONS,
)


def test_expected_cash_basic():
    # Float 100.00 + cash sales 148.05, no movements/refunds.
    exp = expected_cash(opening_float="100.00", cash_sales="148.05",
                        paid_in=0, paid_out=0, cash_refunds=0)
    assert exp == Decimal("248.05")


def test_expected_cash_with_paid_in_out_and_refunds():
    # 100 float + 200 cash sales + 50 paid-in - 30 paid-out - 12.50 refund = 307.50
    exp = expected_cash("100", "200", "50", "30", "12.50")
    assert exp == Decimal("307.50")


def test_close_exact_is_within_tolerance():
    r = close_result(expected="248.05", counted="248.05")
    assert r["variance"] == Decimal("0.00")
    assert r["within_tolerance"] is True
    assert r["short"] is False


def test_close_within_20_rappen_passes():
    # 15 rappen over -> green at the 0.20 tolerance.
    r = close_result(expected="248.05", counted="248.20")
    assert r["variance"] == Decimal("0.15")
    assert r["within_tolerance"] is True


def test_close_just_outside_tolerance_flags():
    # 25 rappen short -> flagged.
    r = close_result(expected="248.05", counted="247.80")
    assert r["variance"] == Decimal("-0.25")
    assert r["within_tolerance"] is False
    assert r["short"] is True


def test_close_exactly_at_tolerance_edge_passes():
    # Exactly 0.20 over -> still within (<=).
    r = close_result(expected="100.00", counted="100.20")
    assert r["variance"] == Decimal("0.20")
    assert r["within_tolerance"] is True


def test_denoms_total_notes_and_coins():
    # 2x50 + 1x20 + 3x5 + 11x0.05 = 100 + 20 + 15 + 0.55 = 135.55
    total = denoms_total({"50": 2, "20": 1, "5": 3, "0.05": 11})
    assert total == Decimal("135.55")


def test_denoms_total_ignores_junk_and_unknown():
    total = denoms_total({"50": 2, "37": 5, "0.05": "x", "20": -3, "bad": 1})
    assert total == Decimal("100.00")  # only the 2x50 counts


def test_denoms_total_not_a_dict():
    assert denoms_total(None) == Decimal("0")
    assert denoms_total("nope") == Decimal("0")


def test_money_rounds_half_up():
    assert money("1.005") == Decimal("1.01")
    assert money("1.004") == Decimal("1.00")


def test_all_chf_denominations_present():
    # Sanity: the grid covers 1000 down to 0.05, 13 denominations.
    assert len(CHF_DENOMINATIONS) == 13
    assert CHF_DENOMINATIONS[0] == Decimal("1000")
    assert CHF_DENOMINATIONS[-1] == Decimal("0.05")
