"""
Custom (non-catalog) line item regression tests.

LOCKS the 2026-06-20 fix for the prod 422: a sale containing a product-as-change
treat or a manual catalog entry (no product_id) failed at
POST /transactions/{id}/items because product_id was required. Custom lines now
carry their own name + unit_price, deduct no stock, and price correctly.
"""
from decimal import Decimal

import pytest

from conftest import POS, find_product, get_transaction


def _open_tx(session):
    r = session.post(f"{POS}/transactions", json={})
    r.raise_for_status()
    return r.json()


def test_sale_with_a_change_treat_completes(session):
    """The 'Add Small Item' / product-as-change flow: real product + a custom treat."""
    p = find_product(session, barcode="7610000123456")  # CBD Oil 10%
    assert p
    price = Decimal(str(p["price"]))
    tx = _open_tx(session)

    # Real product line.
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": p["id"], "quantity": 1, "unit_price": str(price), "discount_percent": "0",
    })
    r.raise_for_status()

    # Custom change treat -- no product_id (this used to 422).
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "quantity": 1, "unit_price": "0.50",
        "discount_percent": "0", "name": "Lollipop (Change)",
    })
    assert r.status_code == 200, f"custom line rejected: {r.status_code} {r.text[:120]}"

    # Checkout cash; total = real price + 0.50.
    expected_total = price + Decimal("0.50")
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": str(expected_total + Decimal("5")),
    })
    r.raise_for_status()
    tx_done = r.json()
    assert Decimal(str(tx_done["total"])) == expected_total

    # The custom line shows its real name on the receipt, not "Product".
    full = get_transaction(session, tx["id"])
    names = [li.get("product_name") for li in full["line_items"]]
    assert "Lollipop (Change)" in names, f"custom line name missing: {names}"


def test_custom_line_requires_unit_price(session):
    """A custom line with no unit_price is a 422 (can't price it)."""
    tx = _open_tx(session)
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "quantity": 1, "discount_percent": "0", "name": "Mystery",
    })
    assert r.status_code == 422, f"expected 422 for priceless custom line, got {r.status_code}"


def test_custom_line_deducts_no_stock(session):
    """A custom line must not touch catalog stock (it has no product)."""
    tx = _open_tx(session)
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": None, "quantity": 3, "unit_price": "1.00",
        "discount_percent": "0", "name": "Sticker",
    })
    assert r.status_code == 200
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": "10.00",
    })
    assert r.status_code == 200  # no stock error, no crash
