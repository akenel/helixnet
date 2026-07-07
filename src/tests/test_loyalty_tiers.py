"""Loyalty tier policy — pure unit tests (no app/DB needed).

Locks in that tiers are DATA (Felix owns the numbers via Settings → Discounts), not code:
tier_for_spend resolves from a store policy, falls back to conservative defaults, and the
"highest threshold cleared" rule survives a mis-ordered or zeroed store config.
"""
from decimal import Decimal

from src.services.loyalty_service import tier_for_spend, policy_from_settings


class _FakeStore:
    """Minimal stand-in for StoreSettingsModel (only the loyalty fields matter)."""
    def __init__(self, t1, d1, t2, d2, t3, d3):
        self.loyalty_tier1_threshold, self.loyalty_tier1_discount = t1, d1
        self.loyalty_tier2_threshold, self.loyalty_tier2_discount = t2, d2
        self.loyalty_tier3_threshold, self.loyalty_tier3_discount = t3, d3


def test_defaults_when_no_policy():
    # Code defaults: Silver@500/5, Gold@1000/10, Platinum@2000/15, else Bronze.
    assert tier_for_spend(Decimal("0")) == ("bronze", 0)
    assert tier_for_spend(Decimal("499")) == ("bronze", 0)
    assert tier_for_spend(Decimal("500")) == ("silver", 5)
    assert tier_for_spend(Decimal("999")) == ("silver", 5)
    assert tier_for_spend(Decimal("1000")) == ("gold", 10)
    assert tier_for_spend(Decimal("1999")) == ("gold", 10)
    assert tier_for_spend(Decimal("2000")) == ("platinum", 15)
    assert tier_for_spend(Decimal("9999")) == ("platinum", 15)


def test_none_store_falls_back_to_defaults():
    assert policy_from_settings(None) is None
    assert tier_for_spend(Decimal("1200"), None) == ("gold", 10)


def test_store_policy_is_honoured():
    # Felix's custom numbers: Silver@300/8, Gold@1500/12, Platinum@4000/20.
    pol = policy_from_settings(_FakeStore(300, 8, 1500, 12, 4000, 20))
    assert tier_for_spend(Decimal("299"), pol) == ("bronze", 0)
    assert tier_for_spend(Decimal("300"), pol) == ("silver", 8)
    assert tier_for_spend(Decimal("1499"), pol) == ("silver", 8)
    assert tier_for_spend(Decimal("1500"), pol) == ("gold", 12)
    assert tier_for_spend(Decimal("4000"), pol) == ("platinum", 20)


def test_bronze_when_lowest_threshold_not_reached():
    pol = policy_from_settings(_FakeStore(500, 5, 1000, 10, 2000, 15))
    assert tier_for_spend(Decimal("100"), pol) == ("bronze", 0)


def test_highest_cleared_threshold_wins_even_if_misordered():
    # Out-of-order thresholds still resolve to the DISCOUNT of the highest threshold the spend
    # clears — money is always the top rung reached, and it never crashes. (Real configs are
    # sane silver<gold<platinum via the UI; this just guards against a fat-fingered save.)
    pol = policy_from_settings(_FakeStore(2000, 15, 500, 5, 1000, 10))
    assert tier_for_spend(Decimal("2500"), pol)[1] == 15   # clears 2000 (highest) -> 15%
    assert tier_for_spend(Decimal("600"), pol)[1] == 5     # clears only 500 -> 5%
    assert tier_for_spend(Decimal("100"), pol) == ("bronze", 0)


def test_zeroed_thresholds_do_not_crash():
    # An all-zero config (fresh row) → everyone clears the lowest rung; never raises.
    pol = policy_from_settings(_FakeStore(0, 0, 0, 0, 0, 0))
    name, pct = tier_for_spend(Decimal("50"), pol)
    assert isinstance(name, str) and isinstance(pct, int)
