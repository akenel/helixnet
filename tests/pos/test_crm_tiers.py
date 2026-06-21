"""
CRM Phase 0a — the conservative 3-tier spend policy (pure, no DB/app env).

LOCKS the 2026-06-21 decision: Bronze 0% / Silver +5% @ CHF 500 / Gold +10% @ CHF 2000,
with a hard 10% standing-discount ceiling ("don't give the store away").
"""
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.services.loyalty_service import tier_for_spend  # noqa: E402


def test_bronze_is_points_only():
    assert tier_for_spend("0") == ("bronze", 0)
    assert tier_for_spend("499.99") == ("bronze", 0)   # still Bronze just under Silver


def test_silver_at_500_is_5_percent():
    assert tier_for_spend("500") == ("silver", 5)
    assert tier_for_spend("1999.99") == ("silver", 5)


def test_gold_at_2000_is_10_percent():
    assert tier_for_spend("2000") == ("gold", 10)
    assert tier_for_spend("10000") == ("gold", 10)


def test_standing_discount_ceiling_is_10_percent():
    for spend in ["0", "500", "2000", "5000", "50000"]:
        _, pct = tier_for_spend(spend)
        assert pct <= 10, f"spend {spend} gave {pct}% -- exceeds the 10% ceiling"


def test_decimal_and_none_inputs_are_safe():
    assert tier_for_spend(Decimal("750")) == ("silver", 5)
    assert tier_for_spend(None) == ("bronze", 0)
