"""
CRM Phase 0b — the sale knows its customer: attach at checkout, auto tier-discount,
earn 1 credit/CHF, update lifetime spend + re-tier.

LOCKS the 2026-06-21 wire-up. Uses the existing customer API (/api/v1/customers) +
the POS checkout. Custom no-stock line items keep the money math deterministic.
"""
import uuid
from decimal import Decimal

from conftest import POS, API_BASE

CUST = f"{API_BASE}/api/v1/customers"


def _new_customer(session):
    """Create a fresh Bronze member (unique handle per run)."""
    handle = "tester_" + uuid.uuid4().hex[:8]
    r = session.post(CUST, json={"handle": handle})
    r.raise_for_status()
    return r.json()["id"]


def _view(session, cid):
    r = session.get(f"{CUST}/checkout/{cid}")
    r.raise_for_status()
    return r.json()


def _ring(session, price, customer_id=None):
    """Ring a custom (no-stock) card sale, optionally attaching a member. Returns the tx."""
    tx = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "name": "CRM test item", "unit_price": str(price), "quantity": 1,
    }).raise_for_status()
    payload = {"payment_method": "visa"}
    if customer_id:
        payload["customer_id"] = customer_id
    done = session.post(f"{POS}/transactions/{tx['id']}/checkout", json=payload)
    done.raise_for_status()
    return done.json()


def test_checkout_attaches_customer_earns_credits_and_retiers(session):
    cid = _new_customer(session)
    before = _view(session, cid)
    assert before["loyalty_tier"] == "bronze"
    assert before["tier_discount_percent"] == 0
    base_credits = before["credits_balance"]      # welcome bonus

    # A CHF 600 sale: Bronze pays full (discount kicks in NEXT time), earns 600 credits,
    # and lifetime spend 600 -> Silver.
    tx = _ring(session, "600.00", customer_id=cid)
    assert Decimal(str(tx["total"])) == Decimal("600.00"), "Bronze: no standing discount yet"
    assert str(tx.get("customer_id")) == cid, "the sale is tied to the member"

    after = _view(session, cid)
    assert after["credits_balance"] == base_credits + 600, "1 credit per CHF"
    assert after["loyalty_tier"] == "silver", "CHF 600 lifetime -> Silver"
    assert after["tier_discount_percent"] == 5


def test_tier_discount_applies_on_the_next_sale(session):
    cid = _new_customer(session)
    _ring(session, "600.00", customer_id=cid)          # -> Silver (5%)
    bal = _view(session, cid)["credits_balance"]

    # Now Silver: a CHF 100 sale is discounted 5% -> pays 95.00, earns 95 credits.
    tx = _ring(session, "100.00", customer_id=cid)
    assert Decimal(str(tx["total"])) == Decimal("95.00"), "Silver 5% applied at the till"
    assert Decimal(str(tx["discount_amount"])) >= Decimal("5.00")
    assert _view(session, cid)["credits_balance"] == bal + 95


def test_gold_at_2000_is_ten_percent(session):
    cid = _new_customer(session)
    _ring(session, "2000.00", customer_id=cid)         # -> Gold (10%)
    assert _view(session, cid)["loyalty_tier"] == "gold"
    tx = _ring(session, "100.00", customer_id=cid)
    assert Decimal(str(tx["total"])) == Decimal("90.00"), "Gold 10% applied"


def test_checkout_without_customer_is_unchanged(session):
    tx = _ring(session, "50.00")                        # no member
    assert Decimal(str(tx["total"])) == Decimal("50.00")
    assert tx.get("customer_id") in (None, "")


def test_unknown_customer_id_is_404(session):
    txn = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{txn['id']}/items", json={
        "product_id": None, "name": "x", "unit_price": "10", "quantity": 1}).raise_for_status()
    r = session.post(f"{POS}/transactions/{txn['id']}/checkout", json={
        "payment_method": "visa", "customer_id": str(uuid.uuid4())})
    assert r.status_code == 404
