"""
BL-83: the transactions report must name WHO rang each sale.

Felix (live, 2026-06-21) saw every row labelled the generic "Cashier". cashier_id is
the Keycloak sub, which equals users.id -- the list endpoint now resolves it to a
display name (first name, else username). LOCKS: a sale rung by felix comes back tagged
'Felix', not a generic literal.
"""
from decimal import Decimal

import pytest

from conftest import POS, ring_sale, list_products


def _an_instock_product(session):
    for p in list_products(session):
        if (p.get("stock_quantity") or 0) > 5 and p.get("price"):
            return p
    pytest.skip("no in-stock product to sell")


def test_transactions_carry_resolved_cashier_name(session):
    """The session rings as felix -> the listed transaction must name a real cashier."""
    prod = _an_instock_product(session)
    tx = ring_sale(session, [(prod["id"], 1, Decimal(str(prod["price"])))],
                   payment_method="twint")  # non-cash: no amount_tendered needed

    rows = session.get(f"{POS}/transactions").json()
    mine = next((r for r in rows if r["id"] == tx["id"]), None)
    assert mine is not None, "rung transaction not found in today's list"

    name = mine.get("cashier_name")
    assert name, "transaction is missing a resolved cashier_name"
    assert name != "Cashier", "still showing the generic 'Cashier' literal"
    # session authenticates as felix -> first_name 'Felix'
    assert name.lower().startswith("felix"), f"expected felix's name, got {name!r}"
