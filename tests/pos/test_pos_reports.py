"""
Daily report / Banana CSV regression tests.

LOCKS: daily summary carries vat_total (the Z-report VAT line); the Banana CSV
requires auth, has the right headers, and its per-method amounts sum to the total.
"""
import csv
import io
from decimal import Decimal

import pytest
import requests

from conftest import POS, API_BASE


def test_daily_summary_has_vat_total(session):
    r = session.get(f"{POS}/reports/daily-summary")
    r.raise_for_status()
    s = r.json()
    assert "vat_total" in s, "daily summary missing vat_total (Z-report VAT line)"
    assert Decimal(str(s["vat_total"])) >= 0


def test_daily_summary_methods_sum_to_total(session):
    r = session.get(f"{POS}/reports/daily-summary")
    r.raise_for_status()
    s = r.json()
    methods = sum(
        Decimal(str(s.get(k, 0)))
        for k in ("cash_total", "twint_total", "visa_total",
                  "debit_total", "bank_transfer_total", "crypto_total", "other_total")
    )
    total = Decimal(str(s.get("total_sales", 0)))
    assert methods == total, f"payment methods {methods} != total_sales {total}"


def test_partial_refund_keeps_net_in_daily_total(session):
    """Regression for '219d42a1 Report totals are wrong': a partial refund must leave the
    NET (kept) amount in the day's total_sales, not erase the whole original sale. Measures
    the report delta around one ring + partial refund (pytest runs serially, so the delta
    is just this test's own activity)."""
    import uuid
    before = Decimal(str(session.get(f"{POS}/reports/daily-summary").json()["total_sales"]))

    prod = session.post(f"{POS}/products", json={
        "sku": "TEST-RPT-" + uuid.uuid4().hex[:8], "name": "TEST report widget",
        "price": "20.00", "stock_quantity": 10}).json()
    tx = session.post(f"{POS}/transactions", json={}).json()
    session.post(f"{POS}/transactions/{tx['id']}/items", json={
        "product_id": prod["id"], "quantity": 2, "unit_price": "20.00"}).raise_for_status()
    session.post(f"{POS}/transactions/{tx['id']}/checkout",
                 json={"payment_method": "visa"}).raise_for_status()  # total 40.00

    r = session.post(f"{POS}/transactions/{tx['id']}/refund",
                     json={"reason": "TEST goodwill", "partial_amount": "10.00"})
    r.raise_for_status()
    assert r.json()["status"] == "completed"

    after = Decimal(str(session.get(f"{POS}/reports/daily-summary").json()["total_sales"]))
    assert after - before == Decimal("30.00"), \
        f"partial refund should keep net 30.00 in the day's total, got delta {after - before}"


def test_csv_requires_auth():
    """Raw URL with NO token must be rejected -- explains the test-sheet 'Not authenticated'."""
    r = requests.get(f"{POS}/reports/daily-summary.csv", verify=False, timeout=15)
    assert r.status_code in (401, 403), f"CSV should require auth, got {r.status_code}"


def test_csv_has_banana_headers_and_sums(session):
    r = session.get(f"{POS}/reports/daily-summary.csv")
    r.raise_for_status()
    assert "text/csv" in r.headers.get("content-type", "")

    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows, "empty CSV"
    assert rows[0] == ["Date", "Description", "Income", "Expenses", "Account", "VatCode"], \
        f"unexpected headers: {rows[0]}"

    # Income column of every data row should sum to the day's total_sales.
    summary = session.get(f"{POS}/reports/daily-summary").json()
    total = Decimal(str(summary.get("total_sales", 0)))
    csv_income = sum(Decimal(row[2]) for row in rows[1:] if row and row[2])
    assert csv_income == total, f"CSV income {csv_income} != total_sales {total}"
