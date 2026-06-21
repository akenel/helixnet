"""
Banco Phase 2 WS-1 -- multi-department under one roof (head shop + cafe + grow).

LOCKS: a sale carries a department; opening a cart defaults to head_shop and
accepts 'cafe'; the daily Z-report splits takings per counter and the split sums
back to total_sales (so the cafe's books and the head shop's books don't blur).
"""
from decimal import Decimal

from conftest import POS, list_products, ring_sale


def test_open_cart_defaults_to_head_shop(session):
    """A cart opened with no department is head_shop -- today's single-counter behaviour."""
    r = session.post(f"{POS}/transactions", json={})
    r.raise_for_status()
    assert r.json().get("department") == "head_shop"


def test_open_cart_accepts_cafe(session):
    """The cafe till opens a cart on the cafe counter."""
    r = session.post(f"{POS}/transactions", json={"department": "cafe"})
    r.raise_for_status()
    assert r.json().get("department") == "cafe"


def test_open_cart_rejects_unknown_department(session):
    """An unknown counter is a validation error, not a silent default."""
    r = session.post(f"{POS}/transactions", json={"department": "casino"})
    assert r.status_code == 422, f"expected 422 for bad department, got {r.status_code}"


def test_daily_summary_by_department_sums_to_total(session):
    """Ring one cafe sale + one head_shop sale; the by_department split must appear
    and sum to total_sales."""
    products = [p for p in list_products(session) if (p.get("stock_quantity") or 0) > 1]
    assert products, "no in-stock product to ring"
    product = products[0]
    pid, price = product["id"], Decimal(str(product["price"]))
    tender = price + Decimal("100")  # cash checkout requires amount_tendered >= total

    ring_sale(session, [(pid, 1, price)], amount_tendered=tender, department="cafe")
    ring_sale(session, [(pid, 1, price)], amount_tendered=tender, department="head_shop")

    s = session.get(f"{POS}/reports/daily-summary").json()
    by_dept = s.get("by_department")
    assert isinstance(by_dept, dict) and by_dept, "daily summary missing by_department split"
    assert "cafe" in by_dept, "cafe sale not reflected in by_department"

    split = sum(Decimal(str(v)) for v in by_dept.values())
    total = Decimal(str(s.get("total_sales", 0)))
    assert split == total, f"by_department {split} != total_sales {total}"
