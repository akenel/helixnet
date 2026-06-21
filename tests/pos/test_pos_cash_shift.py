"""
Per-cashier cash shift (the lockbox loop): open with a float -> ring sales ->
paid-in/out -> close by counting the drawer. Locks the money story:
expected = float + cash sales + paid-in - paid-out - refunds; variance within
CHF 0.20 = green, outside needs a note; each cashier owns their own drawer.

Black-box HTTP against the running server (real Keycloak tokens). felix is the
primary cashier; pam is a second cashier used to prove isolation.
"""
from decimal import Decimal

import pytest
import requests

from conftest import POS, KC_BASE, REALM, CLIENT_ID, find_product, ring_sale

requests.packages.urllib3.disable_warnings()


def _token(username):
    r = requests.post(
        f"{KC_BASE}/realms/{REALM}/protocol/openid-connect/token",
        data={"client_id": CLIENT_ID, "username": username,
              "password": "helix_pass", "grant_type": "password"},
        verify=False, timeout=15)
    r.raise_for_status()
    return r.json()["access_token"]


def _sess(username):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_token(username)}"})
    s.verify = False
    return s


def _ensure_closed(session):
    """Close any leftover open shift (from a prior failed run) at exact expected."""
    cur = session.get(f"{POS}/shift/current", timeout=15).json()
    if cur.get("open"):
        session.post(f"{POS}/shift/close",
                     json={"counted_cash": cur["expected_cash"], "note": "auto-clean prior test shift"},
                     timeout=15)


@pytest.fixture
def felix():
    s = _sess("felix")
    _ensure_closed(s)
    yield s
    _ensure_closed(s)


def test_open_ring_close_balances(felix):
    op = felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"}).json()
    assert op["ok"] is True
    assert op["opening_float"] == "100.00"

    p = find_product(felix, barcode="7610000123461") or find_product(felix, sku="CBD-Oil-20ml")
    price = Decimal(str(p["price"]))
    ring_sale(felix, [(p["id"], 1, price)], payment_method="cash",
              amount_tendered=price + Decimal("10"))

    cur = felix.get(f"{POS}/shift/current").json()
    assert cur["open"] is True
    assert Decimal(cur["expected_cash"]) == Decimal("100.00") + price
    assert Decimal(cur["cash_sales"]) == price

    counted = Decimal("100.00") + price
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": str(counted)}).json()
    assert res["within_tolerance"] is True
    assert Decimal(res["variance"]) == Decimal("0.00")
    assert Decimal(res["expected_cash"]) == counted
    assert res["hours"] >= 0


def test_open_with_denominations_totals_the_float(felix):
    # 2x50 + 11x0.05 = 100.55
    op = felix.post(f"{POS}/shift/open", json={"opening_denoms": {"50": 2, "0.05": 11}}).json()
    assert op["opening_float"] == "100.55"
    cur = felix.get(f"{POS}/shift/current").json()
    assert Decimal(cur["opening_float"]) == Decimal("100.55")


def test_paid_in_out_changes_expected(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "30.00", "reason": "milk for the back"})
    felix.post(f"{POS}/shift/paid", json={"kind": "paid_in", "amount": "10.00", "reason": "change top-up"})
    cur = felix.get(f"{POS}/shift/current").json()
    # 100 - 30 + 10 = 80 (no sales rung)
    assert Decimal(cur["expected_cash"]) == Decimal("80.00")
    assert Decimal(cur["paid_out_total"]) == Decimal("30.00")
    assert Decimal(cur["paid_in_total"]) == Decimal("10.00")
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": "80.00"}).json()
    assert res["within_tolerance"] is True


def test_within_20_rappen_passes_without_note(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    # counted 15 rappen over -> green at 0.20 tolerance, no note needed
    res = felix.post(f"{POS}/shift/close", json={"counted_cash": "100.15"}).json()
    assert res["within_tolerance"] is True
    assert Decimal(res["variance"]) == Decimal("0.15")


def test_outside_tolerance_requires_note(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    # 2.00 short, no note -> blocked
    r = felix.post(f"{POS}/shift/close", json={"counted_cash": "98.00"})
    assert r.status_code == 400
    assert "note" in r.text.lower()
    # still open -> closing WITH a note succeeds and records the variance
    r2 = felix.post(f"{POS}/shift/close",
                    json={"counted_cash": "98.00", "note": "two short, gave wrong change once"}).json()
    assert r2["within_tolerance"] is False
    assert Decimal(r2["variance"]) == Decimal("-2.00")
    assert r2["short"] is True


def test_double_open_is_rejected(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    r = felix.post(f"{POS}/shift/open", json={"opening_float": "50.00"})
    assert r.status_code == 400
    assert "already" in r.text.lower()


def test_close_without_open_is_404(felix):
    # fixture already ensured closed
    r = felix.post(f"{POS}/shift/close", json={"counted_cash": "0"})
    assert r.status_code == 404


def test_paid_requires_kind_amount_reason(felix):
    felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    assert felix.post(f"{POS}/shift/paid", json={"kind": "bogus", "amount": "5", "reason": "x y"}).status_code == 400
    assert felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "0", "reason": "x y"}).status_code == 400
    assert felix.post(f"{POS}/shift/paid", json={"kind": "paid_out", "amount": "5", "reason": ""}).status_code == 400


def test_shifts_are_per_cashier(felix):
    """Pam's drawer must not see Felix's sales, and vice versa."""
    pam = _sess("pam")
    _ensure_closed(pam)
    try:
        felix.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
        pam.post(f"{POS}/shift/open", json={"opening_float": "200.00"})

        # Felix rings a cash sale; it must land on Felix's drawer only.
        p = find_product(felix, barcode="7610000123461") or find_product(felix, sku="CBD-Oil-20ml")
        price = Decimal(str(p["price"]))
        ring_sale(felix, [(p["id"], 1, price)], payment_method="cash",
                  amount_tendered=price + Decimal("10"))

        fcur = felix.get(f"{POS}/shift/current").json()
        pcur = pam.get(f"{POS}/shift/current").json()
        assert Decimal(fcur["cash_sales"]) == price, "Felix should see his own sale"
        assert Decimal(pcur["cash_sales"]) == Decimal("0.00"), "Pam must NOT see Felix's sale"
        assert Decimal(pcur["expected_cash"]) == Decimal("200.00"), "Pam's drawer is just her float"
    finally:
        _ensure_closed(pam)
