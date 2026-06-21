"""
Receiving / goods-in (BL-91) — scan an item, type the count, stock goes UP.

LOCKS: receiving bumps stock_quantity by exactly the units received and reports
the new on-hand; a batch is atomic (one bad product_id → nothing applied).
"""
import uuid

from conftest import POS, find_product


def test_receiving_bumps_stock(session):
    """Receive +5 of a known item → on-hand rises by exactly 5."""
    p = find_product(session, barcode="7610000123466")  # CBD Tea, clean single barcode
    assert p, "expected CBD Relaxation Tea seed product"
    before = p["stock_quantity"]

    r = session.post(f"{POS}/receiving", json={
        "items": [{"product_id": p["id"], "quantity": 5}],
        "reference": "test delivery",
    })
    assert r.status_code == 200, f"{r.status_code} {r.text[:160]}"
    body = r.json()
    assert body["success"] is True
    assert body["total_units"] == 5
    assert body["lines"][0]["stock_after"] == before + 5

    after = find_product(session, barcode="7610000123466")["stock_quantity"]
    assert after == before + 5, f"stock {before} -> {after}, expected {before + 5}"


def test_receiving_multi_line(session):
    """Two products in one delivery both go up; totals add."""
    a = find_product(session, barcode="7610000123463")
    b = find_product(session, barcode="7610000123466")
    assert a and b
    a_before, b_before = a["stock_quantity"], b["stock_quantity"]

    r = session.post(f"{POS}/receiving", json={"items": [
        {"product_id": a["id"], "quantity": 3},
        {"product_id": b["id"], "quantity": 2},
    ]})
    assert r.status_code == 200, f"{r.status_code} {r.text[:160]}"
    assert r.json()["total_units"] == 5

    assert find_product(session, barcode="7610000123463")["stock_quantity"] == a_before + 3
    assert find_product(session, barcode="7610000123466")["stock_quantity"] == b_before + 2


def test_receiving_is_atomic_on_bad_product(session):
    """A missing product_id fails the whole batch — the good line is NOT applied."""
    good = find_product(session, barcode="7610000123466")
    assert good
    before = good["stock_quantity"]

    r = session.post(f"{POS}/receiving", json={"items": [
        {"product_id": good["id"], "quantity": 4},
        {"product_id": str(uuid.uuid4()), "quantity": 4},  # does not exist
    ]})
    assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text[:120]}"

    after = find_product(session, barcode="7610000123466")["stock_quantity"]
    assert after == before, f"atomicity broken: stock moved {before} -> {after}"


def test_receiving_rejects_zero_quantity(session):
    """Quantity must be >= 1 (422 from the schema)."""
    p = find_product(session, barcode="7610000123466")
    r = session.post(f"{POS}/receiving", json={"items": [{"product_id": p["id"], "quantity": 0}]})
    assert r.status_code == 422
