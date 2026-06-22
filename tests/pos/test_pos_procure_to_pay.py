"""
Procure-to-Pay (the slice Banco actually does today) — Ralph keeps the shelves full.

What exists: a manager onboards a product with a margin (price - cost) on record, and it
is immediately sellable. Banco runs ZERO perpetual inventory — there is no stock-count
low-stock/reorder signal (the count was a lie for ~100% unmarked goods); reordering will
ride on sales VELOCITY (the sales log), not a count, in a later brick. The full vendor
PO -> invoice -> payment loop also lands later (lives in the ISOTTO vertical today).

Manager/admin-gated; the test session is felix = admin.
"""
import uuid
from decimal import Decimal

from conftest import POS


def test_product_carries_margin(session):
    """A manager onboards a product with cost -> margin (price - cost) is on record."""
    p = session.post(f"{POS}/products", json={
        "sku": "TEST-PTP-" + uuid.uuid4().hex[:8],
        "name": "TEST margin item",
        "price": "9.00", "cost": "4.00",
        "stock_quantity": 1,
    })
    p.raise_for_status()
    p = p.json()
    assert Decimal(str(p["price"])) - Decimal(str(p["cost"])) == Decimal("5.00")


def test_new_product_is_immediately_sellable(session):
    """Onboard a product -> it shows in search -> it rings up at the price Ralph set."""
    sku = "TEST-NEW-" + uuid.uuid4().hex[:8]
    p = session.post(f"{POS}/products", json={
        "sku": sku, "name": "TEST shiny new line",
        "price": "7.50", "stock_quantity": 30,
    })
    p.raise_for_status()
    pid = p.json()["id"]

    # findable in search
    found = session.get(f"{POS}/search", params={"q": "shiny new line"})
    found.raise_for_status()
    items = found.json()["items"]   # fuzzy /search returns {items: [...]}
    assert any(row.get("sku") == sku for row in items), "new product is searchable"

    # rings up at the set price
    tx = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": pid, "quantity": 1, "unit_price": "7.50"}).raise_for_status()
    done = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={"payment_method": "visa"})
    done.raise_for_status()
    assert Decimal(str(done.json()["total"])) == Decimal("7.50")
