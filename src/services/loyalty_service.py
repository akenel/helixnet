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

# Default rungs (threshold, tier_name, discount_pct) — used when NO store policy is passed
# (host-venv unit tests, or a store with no settings row). Felix owns the real numbers via
# Settings → Discounts; the code only supplies a sane fallback. Names match LoyaltyTier values.
_DEFAULT_RUNGS = (
    (Decimal("2000"), "platinum", 15),
    (Decimal("1000"), "gold", 10),
    (Decimal("500"), "silver", 5),
)


def policy_from_settings(store) -> tuple | None:
    """Build the tier rungs from a StoreSettings row (None → use defaults). The 3 configurable
    settings tiers map to silver/gold/platinum; anyone below tier1 is bronze (points only)."""
    if store is None:
        return None
    return (
        (Decimal(str(store.loyalty_tier3_threshold or 0)), "platinum", int(store.loyalty_tier3_discount or 0)),
        (Decimal(str(store.loyalty_tier2_threshold or 0)), "gold",     int(store.loyalty_tier2_discount or 0)),
        (Decimal(str(store.loyalty_tier1_threshold or 0)), "silver",   int(store.loyalty_tier1_discount or 0)),
    )


def tier_for_spend(lifetime_spend, policy=None) -> tuple[str, int]:
    """(tier_name, discount_percent) for a given lifetime spend. `policy` is the rungs from the
    store settings (Felix's numbers); falls back to conservative defaults. The HIGHEST threshold
    the spend clears wins — so a mis-ordered or zeroed store config still resolves sanely."""
    spend = lifetime_spend if isinstance(lifetime_spend, Decimal) else Decimal(str(lifetime_spend or 0))
    rungs = policy or _DEFAULT_RUNGS
    best_name, best_pct, best_threshold = "bronze", 0, Decimal("-1")
    for threshold, name, pct in rungs:
        if spend >= threshold and threshold > best_threshold:
            best_name, best_pct, best_threshold = name, int(pct), threshold
    return (best_name, best_pct)
