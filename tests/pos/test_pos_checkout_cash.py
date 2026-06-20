"""
Cash payment guard regression tests.

LOCKS: an UNDERPAID cash sale (amount_tendered < total) must never complete.
Angel found the till happily showing a negative change (-0.29) with the Confirm
button live. The server is the backstop (400); the client blocks it too.
"""
from decimal import Decimal

import pytest

from conftest import POS, find_product


def _open_tx(session):
    r = session.post(f"{POS}/transactions", json={})
    r.raise_for_status()
    return r.json()


def test_underpaid_cash_is_rejected(session):
    """Cash tendered below the total is a 400 -- never a completed (underpaid) sale."""
    p = find_product(session, barcode="7610000123457")  # CBD Oil 20%, 89.90
    assert p
    price = Decimal(str(p["price"]))
    tx = _open_tx(session)
    r = session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": p["id"], "quantity": 1, "discount_percent": "0",
    })
    r.raise_for_status()

    # Tender LESS than the total.
    short = (price - Decimal("5")).quantize(Decimal("0.01"))
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": str(short),
    })
    assert r.status_code == 400, f"underpaid cash should be 400, got {r.status_code}"
    assert "payment" in r.text.lower() or "insufficient" in r.text.lower()


def test_exact_cash_completes(session):
    """Tendering exactly the total completes with zero change."""
    p = find_product(session, barcode="7610000123463")  # RAW tips, cheap
    price = Decimal(str(p["price"]))
    tx = _open_tx(session)
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": p["id"], "quantity": 1, "discount_percent": "0",
    }).raise_for_status()
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={
        "payment_method": "cash", "amount_tendered": str(price),
    })
    assert r.status_code == 200, f"exact cash should complete, got {r.status_code} {r.text[:120]}"
    assert Decimal(str(r.json().get("change_given") or "0")) == Decimal("0.00")
