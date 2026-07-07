"""Discount cap is read LIVE from settings — the till no longer hardcodes 10/25.

The phantom-setting bug (round 2): 1851eb4 fixed the checkout ENFORCEMENT to read the
store's per-role caps, but the till UI still hardcoded cashier=10, so an admin raising
pam's cap in Settings had no effect on screen — she was still clamped at 10%. The till now
reads GET /discount-cap, which returns the exact value the server enforces.

  cashier -> cashier_max_discount   manager -> manager_max_discount   admin -> 100
"""
import requests
from conftest import POS, _get_token, _timeout_wrapper

SETTINGS = f"{POS}/settings/1"
CAP = f"{POS}/discount-cap"


def _sess(username):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_get_token(username)}"})
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _cap(s):
    r = s.get(CAP)
    assert r.status_code == 200, r.text
    return float(r.json()["max_discount_pct"])


def test_cashier_cap_tracks_the_live_setting():
    admin = _sess("felix")
    orig = admin.get(SETTINGS).json()
    base = float(orig["cashier_max_discount"] or 10)
    try:
        admin.put(SETTINGS, json={"cashier_max_discount": 33.33})
        assert _cap(_sess("pam")) == 33.33     # the exact value Angel set, live — not 10
    finally:
        admin.put(SETTINGS, json={"cashier_max_discount": base})


def test_manager_cap_tracks_the_live_setting():
    admin = _sess("felix")
    base = float(admin.get(SETTINGS).json()["manager_max_discount"] or 25)
    try:
        admin.put(SETTINGS, json={"manager_max_discount": 42})
        assert _cap(_sess("ralph")) == 42.0
    finally:
        admin.put(SETTINGS, json={"manager_max_discount": base})


def test_admin_is_unlimited():
    assert _cap(_sess("felix")) == 100.0
