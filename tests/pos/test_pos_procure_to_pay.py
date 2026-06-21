"""
Procure-to-Pay (the slice Banco actually does today) — Ralph keeps the shelves full.

What exists: a manager onboards a product, the low-stock signal fires when it dips below
its threshold, and a restock (raise stock_quantity) clears it. Margin = price - cost is
on record. The full vendor PO -> invoice -> payment loop is a LATER brick (lives in the
ISOTTO vertical today, not wired to Banco) -- intentionally not tested here.

Manager/admin-gated; the test session is felix = admin.
"""
import uuid
from decimal import Decimal

from conftest import POS


def _pulse_low_stock(session):
    r = session.get(f"{POS}/system/pulse")
    r.raise_for_status()
    return r.json()["low_stock"]


def test_low_stock_signal_fires_and_restock_clears_it(session):
    """A product below its alert threshold counts as low; restocking above it clears."""
    before = _pulse_low_stock(session)

    # born below threshold: stock 1, alert at 5 -> it's low
    p = session.post(f"{POS}/products", json={
        "sku": "TEST-PTP-" + uuid.uuid4().hex[:8],
        "name": "TEST restock item",
        "price": "9.00", "cost": "4.00",
        "stock_quantity": 1, "stock_alert_threshold": 5,
    })
    p.raise_for_status()
    p = p.json()
    assert _pulse_low_stock(session) == before + 1, "the new low product is counted"

    # margin is on record
    assert Decimal(str(p["price"])) - Decimal(str(p["cost"])) == Decimal("5.00")

    # Ralph receives goods -> raise stock above threshold
    up = session.put(f"{POS}/products/{p['id']}", json={"stock_quantity": 50})
    up.raise_for_status()
    assert up.json()["stock_quantity"] == 50

    assert _pulse_low_stock(session) == before, "restock cleared the low-stock flag"


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
