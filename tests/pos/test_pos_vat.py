"""
Inclusive Swiss VAT regression tests.

LOCKS the 2026-06-20 fix: shelf prices ALREADY include VAT. The gross IS the
total; VAT is the contained portion (gross * rate / (100 + rate)). These tests
would have gone RED on the old additive code (total = net + VAT) that rang a
CHF 89.90 item up as CHF 97.18 and printed a net-only receipt.
"""
from decimal import Decimal

import pytest

from conftest import POS, find_product, ring_sale, get_transaction, inclusive_vat


def test_single_item_total_is_gross_shelf_price(session):
    """A CHF 89.90 item must ring a TOTAL of 89.90 -- not 97.18 (additive bug)."""
    p = find_product(session, sku="CBD-Oil-20ml") or find_product(session, barcode="7610000123457")
    assert p, "expected the CBD Oil 20% seed product"
    price = Decimal(str(p["price"]))

    tx = ring_sale(session, [(p["id"], 1, price)], payment_method="cash",
                   amount_tendered=price + Decimal("10"))

    total = Decimal(str(tx["total"]))
    tax = Decimal(str(tx["tax_amount"]))
    assert total == price, f"total {total} should equal gross shelf price {price}"
    assert tax == inclusive_vat(price), f"VAT {tax} should be contained vat {inclusive_vat(price)}"
    # The contained VAT must be LESS than the total (proves it's inclusive, not on top)
    assert tax < total


def test_vat_is_contained_not_added_on_top(session):
    """The smoking-gun assertion: total must NOT be price * (1 + rate)."""
    p = find_product(session, barcode="7610000123457") or find_product(session, sku="CBD-Oil-20ml")
    price = Decimal(str(p["price"]))
    additive_wrong = (price * (Decimal("100") + Decimal("8.1")) / Decimal("100")).quantize(Decimal("0.01"))

    tx = ring_sale(session, [(p["id"], 1, price)], payment_method="cash",
                   amount_tendered=price + Decimal("10"))
    total = Decimal(str(tx["total"]))
    assert total != additive_wrong, f"total {total} is the additive bug value -- VAT added on top!"
    assert total == price


def test_multi_item_total(session):
    """Two items: total = sum of gross prices; VAT contained within the sum."""
    a = find_product(session, barcode="7610000123463")  # RAW tips 1.20
    b = find_product(session, barcode="7610000123458")  # CBD Flower 35.00
    assert a and b
    pa, pb = Decimal(str(a["price"])), Decimal(str(b["price"]))
    expected_total = pa + pb

    tx = ring_sale(session, [(a["id"], 1, pa), (b["id"], 1, pb)],
                   payment_method="visa")
    total = Decimal(str(tx["total"]))
    tax = Decimal(str(tx["tax_amount"]))
    assert total == expected_total, f"{total} != {expected_total}"
    assert tax == inclusive_vat(expected_total)


def test_receipt_payload_has_real_product_name(session):
    """Receipt line items must carry the real product name, not 'Product'."""
    p = find_product(session, barcode="7610000123461")  # Grinder
    price = Decimal(str(p["price"]))
    tx = ring_sale(session, [(p["id"], 1, price)], payment_method="cash",
                   amount_tendered=price + Decimal("5"))
    full = get_transaction(session, tx["id"])
    items = full.get("line_items", [])
    assert items, "transaction should have line items"
    name = items[0].get("product_name")
    assert name and name != "Product", f"line item name was {name!r}"
    assert name == p["name"]
