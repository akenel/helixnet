"""
Order-to-Cash story 9 — the refund: a sale is reversed (status -> REFUNDED) and cash
is returned. Zero perpetual inventory: a sale never deducts a stock count, so a refund
has nothing to put back — it moves money only.

Manager/admin-gated (the test session is felix = admin). Uses a throwaway product so
the stock math is deterministic on the shared DB.
"""
import uuid
from decimal import Decimal

from conftest import POS


def _new_product(session, *, stock, price="10.00", cost=None, threshold=None):
    """Create a fresh catalog product (admin only). Returns the product dict."""
    body = {
        "sku": "TEST-REF-" + uuid.uuid4().hex[:8],
        "name": "TEST refund widget",
        "price": str(price),
        "stock_quantity": stock,
    }
    if cost is not None:
        body["cost"] = str(cost)
    if threshold is not None:
        body["stock_alert_threshold"] = threshold
    r = session.post(f"{POS}/products", json=body)
    r.raise_for_status()
    return r.json()


def _stock(session, pid):
    r = session.get(f"{POS}/products/{pid}")
    r.raise_for_status()
    return r.json()["stock_quantity"]


def _ring(session, pid, qty, unit_price):
    tx = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": pid, "quantity": qty, "unit_price": str(unit_price)}).raise_for_status()
    done = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={"payment_method": "visa"})
    done.raise_for_status()
    return done.json()


def test_full_refund_flips_status_stock_untouched(session):
    """The sale is reversed (status -> REFUNDED). Zero perpetual inventory: the count
    never moved on the sale, so there is nothing to put back on the refund."""
    p = _new_product(session, stock=10, price="12.00")
    assert _stock(session, p["id"]) == 10

    tx = _ring(session, p["id"], qty=3, unit_price="12.00")
    assert _stock(session, p["id"]) == 10, "a sale does not deduct the count"

    r = session.post(f"{POS}/transactions/{tx['id']}/refund", json={"reason": "TEST broken item"})
    r.raise_for_status()
    assert r.json()["status"] == "refunded"
    assert _stock(session, p["id"]) == 10, "refund moves money only — count unchanged"


def test_partial_refund_is_money_only_stock_untouched(session):
    """A refund returns cash but never touches the count (there is no perpetual stock)."""
    p = _new_product(session, stock=10, price="20.00")
    tx = _ring(session, p["id"], qty=2, unit_price="20.00")  # total 40.00; count never moves
    assert _stock(session, p["id"]) == 10

    r = session.post(f"{POS}/transactions/{tx['id']}/refund",
                     json={"reason": "TEST goodwill", "partial_amount": "10.00"})
    r.raise_for_status()
    assert r.json()["status"] == "refunded"
    assert _stock(session, p["id"]) == 10, "refund is money-only — count unchanged"


def test_refund_cannot_exceed_total(session):
    p = _new_product(session, stock=5, price="10.00")
    tx = _ring(session, p["id"], qty=1, unit_price="10.00")
    r = session.post(f"{POS}/transactions/{tx['id']}/refund",
                     json={"reason": "TEST", "partial_amount": "999.00"})
    assert r.status_code == 400


def test_cannot_refund_an_already_refunded_sale(session):
    """Only COMPLETED sales refund -- a second refund on the same tx is rejected."""
    p = _new_product(session, stock=5, price="10.00")
    tx = _ring(session, p["id"], qty=1, unit_price="10.00")
    session.post(f"{POS}/transactions/{tx['id']}/refund", json={"reason": "TEST one"}).raise_for_status()
    again = session.post(f"{POS}/transactions/{tx['id']}/refund", json={"reason": "TEST two"})
    assert again.status_code == 400


def test_refund_unknown_transaction_is_404(session):
    r = session.post(f"{POS}/transactions/{uuid.uuid4()}/refund", json={"reason": "TEST"})
    assert r.status_code == 404
