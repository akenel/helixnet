"""
Giveaway (free treat) tracking regression tests.

Decision 2026-06-20: treats are tracked giveaways -- a real catalog product handed
over FREE. Zero revenue, but stock leaves inventory and the cost is captured for
tax (COGS). These lock that behaviour end to end.
"""
from decimal import Decimal

import pytest

from conftest import POS, find_product, get_transaction


def _treat(session):
    """First in-stock product in the seeded 'Treats' category."""
    r = session.get(f"{POS}/products", params={"category": "Treats", "limit": 50})
    r.raise_for_status()
    treats = [t for t in r.json() if t["stock_quantity"] > 0]
    assert treats, "no seeded Treats found -- did the startup migration run?"
    return treats[0]


def _open_tx(session):
    r = session.post(f"{POS}/transactions", json={})
    r.raise_for_status()
    return r.json()


def test_giveaway_is_free_total_unchanged(session):
    """A real product given as a giveaway rings at CHF 0 and does not change the total."""
    real = find_product(session, barcode="7610000123461")  # grinder 12.90
    price = Decimal(str(real["price"]))
    treat = _treat(session)
    tx = _open_tx(session)

    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": real["id"], "quantity": 1, "discount_percent": "0",
    }).raise_for_status()
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": treat["id"], "quantity": 1, "discount_percent": "0", "is_giveaway": True,
    })
    assert r.status_code == 200, f"giveaway rejected: {r.status_code} {r.text[:120]}"

    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": str(price + Decimal("5")),
    })
    r.raise_for_status()
    assert Decimal(str(r.json()["total"])) == price, "giveaway must not change the total"

    full = get_transaction(session, tx["id"])
    gv = next((li for li in full["line_items"] if li.get("is_giveaway")), None)
    assert gv is not None, "giveaway line not flagged"
    assert Decimal(str(gv["line_total"])) == Decimal("0.00")


def test_giveaway_decrements_real_stock(session):
    """Giving a treat reduces that product's on-hand stock by the quantity given."""
    treat = _treat(session)
    sku = treat["sku"]
    before = treat["stock_quantity"]
    tx = _open_tx(session)
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": treat["id"], "quantity": 1, "discount_percent": "0", "is_giveaway": True,
    }).raise_for_status()
    session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": "5.00",
    }).raise_for_status()

    after = next(t for t in session.get(f"{POS}/products", params={"category": "Treats", "limit": 50}).json()
                 if t["sku"] == sku)["stock_quantity"]
    assert after == before - 1, f"treat stock {before} -> {after}, expected {before - 1}"


def test_giveaway_tracked_in_daily_summary(session):
    """The day's giveaway count + cost (COGS) appear in the summary for tax."""
    treat = _treat(session)
    tx = _open_tx(session)
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": treat["id"], "quantity": 1, "discount_percent": "0", "is_giveaway": True,
    }).raise_for_status()
    session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": "5.00",
    }).raise_for_status()

    s = session.get(f"{POS}/reports/daily-summary").json()
    assert "giveaway_count" in s and "giveaway_cost" in s
    assert s["giveaway_count"] >= 1
    assert Decimal(str(s["giveaway_cost"])) > 0  # the treat's cost was captured
