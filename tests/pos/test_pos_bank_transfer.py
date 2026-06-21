"""
BL-84: bank-transfer payment method + real per-method breakdown.

Felix (live on banco.lapiazza.app, 2026-06-21) reported the daily report lumped every
sale as "cash" and asked for cash / debit / TWINT / and a bank-transfer (invoice/IBAN)
type. LOCKS: a bank_transfer sale serializes as 'bank_transfer', lands in
bank_transfer_total, keeps the Z-report sum invariant, and shows in the Banana CSV.
"""
from decimal import Decimal

import pytest

from conftest import POS, ring_sale, list_products


def _an_instock_product(session):
    for p in list_products(session):
        if (p.get("stock_quantity") or 0) > 5 and p.get("price"):
            return p
    pytest.skip("no in-stock product to sell")


def test_bank_transfer_sale_lands_in_summary(session):
    """A sale paid by bank transfer must move bank_transfer_total by exactly its total
    (delta-measured so it's safe on the shared dev DB)."""
    prod = _an_instock_product(session)

    before = session.get(f"{POS}/reports/daily-summary")
    before.raise_for_status()
    bt_before = Decimal(str(before.json().get("bank_transfer_total", 0)))

    price = Decimal(str(prod["price"]))
    tx = ring_sale(session, [(prod["id"], 1, price)], payment_method="bank_transfer")
    assert tx["payment_method"] == "bank_transfer", \
        f"expected 'bank_transfer', got {tx['payment_method']!r}"

    after = session.get(f"{POS}/reports/daily-summary")
    after.raise_for_status()
    bt_after = Decimal(str(after.json()["bank_transfer_total"]))
    assert bt_after - bt_before == Decimal(str(tx["total"])), \
        f"bank_transfer_total delta {bt_after - bt_before} != sale total {tx['total']}"


def test_summary_methods_still_sum_to_total(session):
    """The Z-report invariant (Σ per-method == total_sales) must still hold with the new
    bank_transfer bucket -- otherwise the day's money is unaccounted for."""
    s = session.get(f"{POS}/reports/daily-summary").json()
    methods = sum(Decimal(str(s.get(k, 0))) for k in (
        "cash_total", "twint_total", "visa_total", "debit_total",
        "bank_transfer_total", "crypto_total", "other_total"))
    assert methods == Decimal(str(s.get("total_sales", 0)))


def test_bank_transfer_in_banana_csv(session):
    """Bank-transfer takings must export to the accountant's CSV, not vanish."""
    r = session.get(f"{POS}/reports/daily-summary.csv")
    r.raise_for_status()
    assert "Bank transfer" in r.text
