"""Kiosk first-order WELCOME discount — applied + consumed at ring-out (banco-kiosk-guest-station v2b).

A guest self-signs-up at the kiosk (10%) or on their phone (15%), builds a held order, and Felix
rings it. The welcome discount comes off the eligible portion EXACTLY ONCE, is marked used, and the
cart is claimed — so it can never be spent twice. Live money path: create_sale with kiosk_cart_code.

Run (sandbox):  ENV=sandbox POS_REALM=kc-sandbox python -m pytest tests/pos/test_pos_kiosk_welcome.py -v
"""
import uuid
from decimal import Decimal

import requests
from conftest import POS, _get_token, _timeout_wrapper


def _sess(username="felix"):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_get_token(username)}"})
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _pub():
    s = requests.Session()
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _signup(source="kiosk"):
    r = _pub().post(f"{POS}/kiosk/signup",
                    json={"handle": "wel_" + uuid.uuid4().hex[:8], "age_confirmed": True, "source": source})
    r.raise_for_status()
    return r.json()


def _held_cart(customer_id):
    """An open held order attached to the member (empty is fine — the welcome lane keys on the cart
    being open + owned by the ringing member, not on its lines)."""
    r = _pub().post(f"{POS}/kiosk/cart", json={"items": [], "customer_id": customer_id, "source": "kiosk"})
    r.raise_for_status()
    return r.json()["code"]


def _ring(s, price, customer_id, code=None):
    body = {
        "client_uuid": str(uuid.uuid4()),
        "lines": [{"product_id": None, "quantity": 1, "unit_price": str(price), "name": "welcome test"}],
        "payment_method": "visa",
        "customer_id": customer_id,
    }
    if code:
        body["kiosk_cart_code"] = code
    return s.post(f"{POS}/sales", json=body)


def test_kiosk_welcome_10_applies_then_never_again():
    m = _signup("kiosk")
    assert m["discount_pct"] == 10
    code = _held_cart(m["id"])
    felix = _sess("felix")
    r = _ring(felix, "100.00", m["id"], code)
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["total"]) == Decimal("90.00"), "10% welcome off CHF 100"
    # ring AGAIN, same member + same code → used + claimed → full price
    r2 = _ring(felix, "100.00", m["id"], code)
    assert r2.status_code == 201, r2.text
    assert Decimal(r2.json()["total"]) == Decimal("100.00"), "welcome must never apply twice"


def test_kiosk_welcome_phone_is_15():
    m = _signup("phone")
    assert m["discount_pct"] == 15
    code = _held_cart(m["id"])
    r = _ring(_sess("felix"), "100.00", m["id"], code)
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["total"]) == Decimal("85.00"), "15% phone welcome off CHF 100"


def test_no_code_means_no_welcome():
    m = _signup("kiosk")
    r = _ring(_sess("felix"), "100.00", m["id"], code=None)   # no held order rung
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["total"]) == Decimal("100.00"), "welcome applies ONLY via a held order code"
