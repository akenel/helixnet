"""
THE headline story — Order-to-Cash, end to end, as one continuous narrative.

This is the release gate's flagship: it walks the whole arc the way Pam lives it, in
order, asserting each link. If this stays green, the core of Felix's business works.

  enroll a member (18+) -> ring a real catalogue sale on their account
  -> stock count is untouched (zero perpetual inventory) -> points earned +
     lifetime grows -> tier climbs to Silver
  -> the NEXT sale gets the 5% member discount -> View History has it on record
  -> the receipt view resolves the buyer.

Uses a throwaway product so the money + stock math is deterministic on the shared DB.
"""
import uuid
from decimal import Decimal

from conftest import POS, API_BASE

CUST = f"{API_BASE}/api/v1/customers"


def _product(session, *, stock, price):
    r = session.post(f"{POS}/products", json={
        "sku": "TEST-O2C-" + uuid.uuid4().hex[:8],
        "name": "TEST o2c item",
        "price": str(price),
        "stock_quantity": stock,
    })
    r.raise_for_status()
    return r.json()


def _stock(session, pid):
    return session.get(f"{POS}/products/{pid}").json()["stock_quantity"]


def _ring(session, pid, qty, unit_price, customer_id=None):
    tx = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": pid, "quantity": qty, "unit_price": str(unit_price)}).raise_for_status()
    payload = {"payment_method": "visa"}
    if customer_id:
        payload["customer_id"] = customer_id
    done = session.post(f"{POS}/transactions/{tx['id']}/checkout", json=payload)
    done.raise_for_status()
    return done.json()


def _member(session, cid):
    r = session.get(f"{CUST}/checkout/{cid}")
    r.raise_for_status()
    return r.json()


def test_order_to_cash_end_to_end(session):
    # --- 1. enroll Johnny (18+ required) ---
    handle = "TEST-johnny-" + uuid.uuid4().hex[:6]
    enroll = session.post(CUST, json={"handle": handle, "age_confirmed": True})
    enroll.raise_for_status()
    cid = enroll.json()["id"]

    start = _member(session, cid)
    assert start["loyalty_tier"] == "bronze"
    assert start["tier_discount_percent"] == 0
    base_credits = start["credits_balance"]

    # --- 2. a real catalogue sale on his account: points land, count never moves ---
    # NOTE: checkout prices catalogue lines from product.price (the till never trusts a
    # client-sent price), so the totals here follow the product's CHF 100.00.
    p = _product(session, stock=20, price="100.00")
    tx1 = _ring(session, p["id"], qty=2, unit_price="100.00", customer_id=cid)  # 200.00
    assert Decimal(str(tx1["total"])) == Decimal("200.00"), "Bronze pays full"
    assert str(tx1["customer_id"]) == cid, "the sale is tied to Johnny"
    assert _stock(session, p["id"]) == 20, "zero perpetual inventory: the count never moves"

    after1 = _member(session, cid)
    assert after1["credits_balance"] == base_credits + 200, "1 credit per CHF"
    assert after1["lifetime_spend"] == 200.0

    # --- 3. cross CHF 500 -> Silver ---
    _ring(session, p["id"], qty=4, unit_price="100.00", customer_id=cid)        # lifetime -> 600
    silver = _member(session, cid)
    assert silver["loyalty_tier"] == "silver"
    assert silver["tier_discount_percent"] == 5

    # --- 4. the NEXT sale gets the standing 5% ---
    tx3 = _ring(session, p["id"], qty=1, unit_price="100.00", customer_id=cid)  # 100 -> 95 (Silver)
    assert Decimal(str(tx3["total"])) == Decimal("95.00"), "Silver 5% applied at the till"
    assert Decimal(str(tx3["discount_amount"])) >= Decimal("5.00")

    # --- 5. View History has it on record (Johnny's lighter) ---
    hist = session.get(f"{CUST}/{cid}/transactions")
    hist.raise_for_status()
    hist = hist.json()
    assert hist["transaction_count"] >= 3, "every sale on his account is on record"
    assert any(it["name"] == "TEST o2c item"
               for t in hist["transactions"] for it in t["items"]), "the items are itemised"

    # --- 6. the receipt resolves the buyer ---
    full = session.get(f"{POS}/transactions/{tx3['id']}").json()
    assert str(full.get("customer_id")) == cid, "the receipt can show who bought"
