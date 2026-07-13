"""Member tier + manual discount = SEPARATE LANES (Felix's call 2026-07-13).

Supersedes the old "Option B" where a member SUPPRESSED the manual discount entirely. The two
discounts are now independent pockets:

  • the member's earned TIER rate — the shop's loyalty promise, automatic, ALWAYS applies and
    stacks on top, UNCAPPED by the cashier's role;
  • the cashier's MANUAL discount — their own discretion / rounding room, bounded by a per-role
    fat-finger cap (cashier 15 / manager 70 / owner 100).

So a platinum member (tier 20-25%) can be served SOLO by a 15%-capped cashier and still get his
full tier (the "George Clooney" case), and a manager can run a big clearance markdown (scratched
display unit) that a cashier cannot — while the member's tier still rides on top of that markdown.

These tests READ the live per-role caps and the member's actual tier % from the target env, then
assert the stacking + fat-finger-cap MATH — so they pass whatever caps/loyalty %s an env carries.

Live path only: POST /api/v1/pos/sales (create_sale). Card (visa) sales need no cash drawer.

Run (sandbox):  ENV=sandbox POS_REALM=kc-sandbox python -m pytest tests/pos/test_pos_member_manual_stack.py -v
"""
import uuid
from decimal import Decimal

import pytest
import requests
from conftest import POS, API_BASE, _get_token, _timeout_wrapper

CUST = f"{API_BASE}/api/v1/customers"


def _sess(username):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_get_token(username)}"})
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _new_customer(s):
    """A fresh Bronze member (0% tier). 18+ is required to enroll."""
    r = s.post(CUST, json={"handle": "stk_" + uuid.uuid4().hex[:8], "age_confirmed": True})
    r.raise_for_status()
    return r.json()["id"]


def _atomic(s, price, customer_id=None, discount_percent="0"):
    """Ring ONE custom (no-stock) line via the live atomic path, card payment (no drawer)."""
    body = {
        "client_uuid": str(uuid.uuid4()),
        "lines": [{"product_id": None, "quantity": 1, "unit_price": str(price),
                   "name": "stack test item"}],
        "payment_method": "visa",
        "discount_percent": str(discount_percent),
    }
    if customer_id:
        body["customer_id"] = customer_id
    return s.post(f"{POS}/sales", json=body)


def _tier_pct(s, cid):
    r = s.get(f"{CUST}/checkout/{cid}")
    r.raise_for_status()
    return Decimal(str(r.json()["tier_discount_percent"]))


def _cap(s):
    r = s.get(f"{POS}/discount-cap")
    r.raise_for_status()
    return Decimal(str(r.json()["max_discount_pct"]))


def _member_at(s, spend):
    """Ring `spend` so the member earns a tier. Returns (cid, tier_pct) read live."""
    cid = _new_customer(s)
    assert _atomic(s, str(spend), customer_id=cid).status_code == 201
    pct = _tier_pct(s, cid)
    assert pct > 0, f"CHF {spend} lifetime should earn a tier discount on any config"
    return cid, pct


def _expected_total(base, *pcts):
    """base minus each pct% of base (all off the same eligible base), cent-rounded per component
    — mirrors the server's per-discount quantize."""
    total = Decimal(str(base))
    for p in pcts:
        total -= (Decimal(str(base)) * Decimal(str(p)) / Decimal("100")).quantize(
            Decimal("0.01"), rounding="ROUND_HALF_UP")
    return total


# --- The exact bug Angel hit on prod (HC-PROD-01 row 10): a manual discount on a member sale. ---

def test_bronze_member_plus_manual_discount_applies(session):
    """Old Option B silently dropped a cashier's manual discount the moment a member was
    attached. Now a Bronze (0% tier) member + a 10% manual = 10% off — the discount is honored."""
    cid = _new_customer(session)                     # Bronze, 0%
    assert _tier_pct(session, cid) == 0
    r = _atomic(session, "100.00", customer_id=cid, discount_percent="10")
    assert r.status_code == 201, r.text
    sale = r.json()
    assert Decimal(sale["total"]) == Decimal("90.00"), "manual 10% must apply on a member sale"
    assert Decimal(sale["discount_amount"]) == Decimal("10.00")
    assert str(sale.get("customer_id")) == cid


# --- Stacking: manual ON TOP of the earned tier rate, off the same eligible base. ---

def test_tier_and_manual_stack(session):
    """A tiered member + a manual % both apply, off the same eligible base (felix=admin, cap 100).
    Assert against the member's ACTUAL earned rate."""
    cid, tier = _member_at(session, "600.00")
    manual = Decimal("5")
    r = _atomic(session, "100.00", customer_id=cid, discount_percent=str(manual))
    assert r.status_code == 201, r.text
    expected = _expected_total("100.00", tier, manual)
    assert Decimal(r.json()["total"]) == expected, f"tier {tier}% + manual {manual}% should stack"


# --- SEPARATE LANES: the tier stacks BEYOND the cashier's own cap. ---

def test_tier_stacks_on_top_of_a_cashier_capped_manual():
    """Pam applies her FULL manual cap; the member's tier rides ON TOP, so the TOTAL discount
    exceeds Pam's cap — and the sale still completes. This is the heart of separate lanes: the
    cap bounds Pam's manual, never the shop's loyalty rate."""
    admin = _sess("felix")
    cid, tier = _member_at(admin, "600.00")
    pam = _sess("pam")
    cap = _cap(pam)
    r = _atomic(pam, "100.00", customer_id=cid, discount_percent=str(cap))   # manual == cashier cap
    assert r.status_code == 201, r.text
    expected = _expected_total("100.00", tier, cap)
    assert Decimal(r.json()["total"]) == expected, "tier must stack on top of the capped manual"
    # On a CHF 100 base the discount amount in CHF equals the total percent — prove it beat the cap.
    assert (Decimal("100.00") - expected) > cap, "total discount should exceed the cashier's cap"


def test_high_tier_member_served_by_cashier_gets_full_tier():
    """The George Clooney case: a top-tier member whose rate may EXCEED the cashier cap is served
    SOLO by the cashier (no manager) and still gets his full tier — the cap never touches it."""
    admin = _sess("felix")
    cid, tier = _member_at(admin, "2000.00")          # top tier
    pam = _sess("pam")
    r = _atomic(pam, "100.00", customer_id=cid, discount_percent="0")
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["total"]) == _expected_total("100.00", tier), "full tier applies solo"


# --- The fat-finger cap bounds the MANUAL discount alone (the "type 2 as a target" guard). ---

def test_cashier_manual_over_own_cap_is_403():
    """A manual over the cashier's own cap is refused — with or without a member. This is the
    fat-finger guard (Layla's 'she types 2 francs by mistake' scenario)."""
    pam = _sess("pam")
    over = _cap(pam) + Decimal("1")
    r = _atomic(pam, "100.00", discount_percent=str(over))     # walk-in, no member
    assert r.status_code == 403, r.text
    assert "limit" in r.text.lower()


def test_safety_floor_never_pays_the_customer():
    """The footgun guard Angel caught: owner cap 100% + a member's tier = >100% combined. On an
    all-eligible cart the total must FLOOR at zero, NEVER go negative — no matter what caps/tiers
    are set. Bad settings upstream can't ever produce a refund at the till."""
    admin = _sess("felix")                              # owner, cap 100
    cid, tier = _member_at(admin, "2000.00")            # top tier (e.g. 25%)
    r = _atomic(admin, "100.00", customer_id=cid, discount_percent="100")   # 100% manual + tier > 100%
    assert r.status_code == 201, r.text
    total = Decimal(r.json()["total"])
    assert total == Decimal("0.00"), f"all-eligible cart must floor at 0, got {total}"
    assert total >= 0, "the till can never owe the customer money"


def test_manager_can_run_a_markdown_the_cashier_cannot():
    """The scratched-display-tray case: a manual over the CASHIER cap but within the MANAGER cap
    is refused for Pam, accepted for Ralph. Layla (manager) clears damaged stock solo; Pam can't."""
    pam, ralph = _sess("pam"), _sess("ralph")
    cash_cap, mgr_cap = _cap(pam), _cap(ralph)
    if mgr_cap <= cash_cap:
        pytest.skip("manager cap not greater than cashier cap on this config")
    manual = cash_cap + Decimal("1")                  # over cashier, within manager
    assert _atomic(pam, "100.00", discount_percent=str(manual)).status_code == 403
    r = _atomic(ralph, "100.00", discount_percent=str(manual))
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["total"]) == _expected_total("100.00", manual)
