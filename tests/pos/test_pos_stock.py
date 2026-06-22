"""
Stock / inventory regression tests.

LOCKS: zero perpetual inventory — a sale NEVER deducts a stock count and is NEVER
blocked by one (the count is a lie for ~100% unmarked goods). The stock_quantity
column still exists but is dormant; velocity comes from the sales log (v2).
"""
from decimal import Decimal

import pytest

from conftest import POS, list_products, find_product, ring_sale


def test_catalog_carries_stock_quantity(session):
    """The stock_quantity column is dormant but still serialized; rows must keep the
    field (an int) so nothing downstream KeyErrors on it during the v1 -> v2 window."""
    products = list_products(session)
    assert products, "no products -- did seeding run?"
    for p in products:
        assert "stock_quantity" in p, f"{p.get('sku')} missing stock_quantity"
        assert isinstance(p["stock_quantity"], int)


def test_checkout_does_not_deduct_stock(session):
    """Zero perpetual inventory: ringing a sale must NOT change stock_quantity. The
    sale lives in the sales log, never against a count."""
    p = find_product(session, barcode="7610000123466")  # CBD Tea, plentiful seed
    assert p, "expected CBD Relaxation Tea seed product"
    before = p["stock_quantity"]

    price = Decimal(str(p["price"]))
    ring_sale(session, [(p["id"], 2, price)], payment_method="visa")

    after = find_product(session, barcode="7610000123466")["stock_quantity"]
    assert after == before, f"a sale must not move the count: {before} -> {after}"


def test_oversell_is_allowed_sell_to_seed(session):
    """BL-94 / Felix #91: a sale is NEVER blocked by a stock count. The count is a
    lie for ~100% unmarked goods, so a real product on the shelf is ALWAYS sellable.
    Adding MORE than on-hand must be accepted (no 400) -- the count never moves and
    never gates a sale."""
    products = list_products(session)
    low = next((p for p in products if 0 <= p["stock_quantity"] <= 3 and p["is_active"]), None)
    if not low:
        pytest.skip("no low-stock active product to test sell-to-seed")

    tx = session.post(f"{POS}/transactions", json={})
    tx.raise_for_status()
    tx = tx.json()
    r = session.post(
        f"{POS}/transactions/{tx['id']}/items",
        json={
            "product_id": low["id"],
            "quantity": low["stock_quantity"] + 5,  # deliberately over on-hand
            "unit_price": str(low["price"]),
            "discount_percent": "0",
        },
    )
    assert r.status_code in (200, 201), \
        f"sell-to-seed: an over-sell must NOT be blocked, got {r.status_code} {r.text[:140]}"
