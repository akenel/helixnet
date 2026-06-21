"""
Loyalty tier policy -- pure, dependency-free (only decimal), so it's trivially
unit-testable from the host venv without the app/Settings chain.

Banco 3-tier spend model (decided 2026-06-21, conservative -- don't give the store
away). Bronze = every member, points only, NO standing discount; Silver at CHF 500
= +5%; Gold at CHF 2000 = +10%. Ceiling is 10% standing (plus ~5% in points).
Returns the tier name (matches LoyaltyTier enum values) + the discount percent.
"""
from decimal import Decimal

SILVER_MIN = Decimal("500")
GOLD_MIN = Decimal("2000")


def tier_for_spend(lifetime_spend) -> tuple[str, int]:
    """(tier_name, discount_percent) for a given lifetime spend."""
    spend = lifetime_spend if isinstance(lifetime_spend, Decimal) else Decimal(str(lifetime_spend or 0))
    if spend >= GOLD_MIN:
        return ("gold", 10)
    if spend >= SILVER_MIN:
        return ("silver", 5)
    return ("bronze", 0)
