"""
Stock / inventory regression tests.

LOCKS: catalog payload carries stock_quantity (so the till can show "N in stock"),
checkout deducts stock by the quantity sold, and stock never goes negative.
"""
from decimal import Decimal

import pytest

from conftest import POS, list_products, find_product, ring_sale


def test_catalog_carries_stock_quantity(session):
    """Every product row must expose stock_quantity (the catalog badge depends on it)."""
    products = list_products(session)
    assert products, "no products -- did seeding run?"
    for p in products:
        assert "stock_quantity" in p, f"{p.get('sku')} missing stock_quantity"
        assert isinstance(p["stock_quantity"], int)


def test_checkout_deducts_stock_by_qty_sold(session):
    """Ring qty 2 of an in-stock item -> stock drops by exactly 2."""
    p = find_product(session, barcode="7610000123466")  # CBD Tea, plentiful seed
    assert p, "expected CBD Relaxation Tea seed product"
    before = p["stock_quantity"]
    if before < 2:
        pytest.skip(f"need >=2 stock to test deduction, have {before}")

    price = Decimal(str(p["price"]))
    ring_sale(session, [(p["id"], 2, price)], payment_method="visa")

    after = find_product(session, barcode="7610000123466")["stock_quantity"]
    assert after == before - 2, f"stock {before} -> {after}, expected {before - 2}"


def test_oversell_is_allowed_sell_to_seed(session):
    """BL-94 / Felix #91: a sale is NEVER blocked by a stock count. The count is a
    lie for ~100% unmarked goods, so a real product on the shelf is ALWAYS sellable.
    Adding MORE than on-hand must be accepted (no 400) -- stock is still tracked and
    deducted (floored at 0), just never a gate."""
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
