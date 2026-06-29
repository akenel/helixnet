"""P2.1 — atomic, idempotent create-sale (`POST /pos/sales`).

Black-box HTTP against the running server (same harness as the rest of tests/pos).
Proves the three things that matter for the offline-outbox keystone:
  1. the whole cart + payment rings in ONE request and completes,
  2. it is IDEMPOTENT on client_uuid — a replay adopts the sale exactly once (never
     double-rings), which is what makes an offline outbox safe to retry,
  3. its money is IDENTICAL to the legacy 3-step path (so the two never drift).

Custom lines (product_id=None + unit_price) are used so the test is self-contained —
no dependency on which catalog happens to be seeded in the target env.

Run (sandbox):  ENV=sandbox POS_REALM=kc-sandbox python -m pytest tests/pos/test_pos_create_sale_atomic.py -v
"""
import uuid
from decimal import Decimal

from conftest import POS, ring_sale


def _line(qty, price, name="Test item"):
    return {"product_id": None, "quantity": qty, "unit_price": str(price), "name": name}


def _atomic_body(client_uuid, lines, payment_method="cash", amount_tendered="50.00",
                 discount_percent="0"):
    body = {
        "client_uuid": client_uuid,
        "lines": lines,
        "payment_method": payment_method,
        "discount_percent": discount_percent,
    }
    if amount_tendered is not None:
        body["amount_tendered"] = amount_tendered
    return body


def test_atomic_sale_completes_in_one_call(session):
    """One POST = a completed sale with the right totals + change."""
    body = _atomic_body(str(uuid.uuid4()), [_line(2, "5.00"), _line(1, "3.50")],
                        amount_tendered="20.00")
    r = session.post(f"{POS}/sales", json=body)
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale["status"] == "completed"
    assert Decimal(sale["subtotal"]) == Decimal("13.50")
    assert Decimal(sale["total"]) == Decimal("13.50")      # no discount
    assert Decimal(sale["change_given"]) == Decimal("6.50")  # 20.00 - 13.50
    assert sale["receipt_number"].startswith("REC-TXN-")


def test_idempotent_replay_rings_exactly_once(session):
    """The SAME client_uuid posted twice must return the SAME sale — not a second one.
    This is the property that lets an offline outbox retry without fear."""
    cu = str(uuid.uuid4())
    body = _atomic_body(cu, [_line(1, "7.25")], amount_tendered="10.00")

    r1 = session.post(f"{POS}/sales", json=body)
    assert r1.status_code == 201, r1.text
    first = r1.json()

    r2 = session.post(f"{POS}/sales", json=body)
    assert r2.status_code in (200, 201), r2.text
    second = r2.json()

    assert first["id"] == second["id"], "replay created a different transaction id"
    assert first["transaction_number"] == second["transaction_number"], "replay rang a second sale"
    assert Decimal(second["total"]) == Decimal("7.25")


def test_atomic_money_matches_legacy_three_step(session):
    """Same cart through the legacy create→items→checkout path and through /sales must
    agree to the cent on subtotal, total AND VAT — one source of truth, two doors."""
    cart = [(None, 2, Decimal("4.25")), (None, 3, Decimal("1.10"))]   # 8.50 + 3.30 = 11.80
    legacy = ring_sale(session, cart, payment_method="cash", amount_tendered="20")

    lines = [_line(q, p) for (_pid, q, p) in cart]
    r = session.post(f"{POS}/sales", json=_atomic_body(str(uuid.uuid4()), lines,
                                                       amount_tendered="20.00"))
    assert r.status_code == 201, r.text
    atomic = r.json()

    for field in ("subtotal", "total", "tax_amount"):
        assert Decimal(atomic[field]) == Decimal(legacy[field]), \
            f"{field} drift: atomic={atomic[field]} legacy={legacy[field]}"


def test_empty_cart_rejected(session):
    """No lines = a 422 at the schema boundary (can't ring nothing)."""
    body = _atomic_body(str(uuid.uuid4()), [], amount_tendered="5.00")
    r = session.post(f"{POS}/sales", json=body)
    assert r.status_code == 422, r.text


def test_card_sale_needs_no_drawer(session):
    """A card/TWINT sale never touches the cash drawer, so it completes with no tender
    and no open-shift gate."""
    body = _atomic_body(str(uuid.uuid4()), [_line(1, "9.90")],
                        payment_method="twint", amount_tendered=None)
    r = session.post(f"{POS}/sales", json=body)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"
