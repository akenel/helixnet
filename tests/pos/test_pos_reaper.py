"""
BL-86: end-of-day reaper for stale empty carts.

Angel spotted dangling OPEN / CHF 0.00 carts cluttering Felix's report -- abandoned
sessions (cashier opens a sale, customer walks). The reaper CANCELS (auditable, never
deletes) carts that are OPEN, zero-value, AND empty, once they're older than N hours.
LOCKS: an old empty cart is cancelled; a cart with items is spared; a fresh empty cart
(under the age threshold) is spared.
"""
from decimal import Decimal

import pytest

from conftest import POS, list_products, get_transaction


def _an_instock_product(session):
    for p in list_products(session):
        if (p.get("stock_quantity") or 0) > 5 and p.get("price"):
            return p
    pytest.skip("no in-stock product to sell")


def _open_cart(session):
    r = session.post(f"{POS}/transactions", json={})
    r.raise_for_status()
    tx = r.json()
    assert tx["status"].lower() == "open"
    return tx


def test_reaper_cancels_old_empty_cart(session):
    """An empty OPEN cart older than the threshold gets CANCELLED (older_than_hours=0
    makes 'a moment ago' qualify)."""
    tx = _open_cart(session)
    r = session.post(f"{POS}/maintenance/reap-empty-carts", params={"older_than_hours": 0})
    r.raise_for_status()
    assert r.json()["cancelled"] >= 1
    assert get_transaction(session, tx["id"])["status"].lower() == "cancelled"


def test_reaper_spares_cart_with_items(session):
    """A cart that has line items is never reaped, even if old/zero-thresholded."""
    prod = _an_instock_product(session)
    tx = _open_cart(session)
    session.post(
        f"{POS}/transactions/{tx['id']}/items",
        json={"product_id": prod["id"], "quantity": 1,
              "unit_price": str(prod["price"]), "discount_percent": "0"},
    ).raise_for_status()

    session.post(f"{POS}/maintenance/reap-empty-carts",
                 params={"older_than_hours": 0}).raise_for_status()

    assert get_transaction(session, tx["id"])["status"].lower() == "open"


def test_reaper_spares_recent_empty_cart(session):
    """A just-opened empty cart is younger than 12h -> left alone."""
    tx = _open_cart(session)
    session.post(f"{POS}/maintenance/reap-empty-carts",
                 params={"older_than_hours": 12}).raise_for_status()
    assert get_transaction(session, tx["id"])["status"].lower() == "open"


def test_cancelled_cart_hidden_from_default_list(session):
    """BL-86: a cancelled cart drops out of the default transactions view, but is still
    reachable with an explicit status filter (cancel != delete)."""
    tx = _open_cart(session)
    session.post(f"{POS}/maintenance/reap-empty-carts",
                 params={"older_than_hours": 0}).raise_for_status()

    default = session.get(f"{POS}/transactions").json()
    assert not any(r["id"] == tx["id"] for r in default), \
        "cancelled cart should be hidden from the default list"

    filtered = session.get(f"{POS}/transactions",
                           params={"status_filter": "cancelled"}).json()
    assert any(r["id"] == tx["id"] for r in filtered), \
        "status_filter=cancelled should surface the cancelled cart"
