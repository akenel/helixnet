"""Store settings — role matrix (Angel's spec).

  cashier  -> view only: can GET, cannot PUT (403)
  manager  -> can PUT general settings, but discount caps are STRIPPED (self-cap risk)
  admin    -> can PUT everything incl. discount caps

The discount seal is enforced SERVER-SIDE, not just by the disabled UI field.
Black-box HTTP against the running server (same harness as the rest of tests/pos).
"""
import requests
from conftest import POS, _get_token, _timeout_wrapper

SETTINGS = f"{POS}/settings/1"


def _sess(username):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {_get_token(username)}"})
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _get(s):
    r = s.get(SETTINGS)
    assert r.status_code == 200, r.text
    return r.json()


# ---- cashier: view only -------------------------------------------------

def test_cashier_can_view_settings():
    s = _sess("pam")
    data = _get(s)                     # GET is any-POS-role
    assert "cashier_max_discount" in data


def test_cashier_cannot_edit_settings():
    s = _sess("pam")
    r = s.put(SETTINGS, json={"store_name": "Hacked By Pam"})
    assert r.status_code == 403, r.text


# ---- manager: edits everything EXCEPT discount caps ---------------------

def test_manager_can_edit_general_settings():
    s = _sess("ralph")
    original = _get(s)["store_name"]
    r = s.put(SETTINGS, json={"store_name": "Manager Edit OK"})
    assert r.status_code == 200, r.text
    assert _get(s)["store_name"] == "Manager Edit OK"
    s.put(SETTINGS, json={"store_name": original})   # restore


def test_manager_discount_change_is_stripped_server_side():
    admin = _sess("felix")
    base = float(_get(admin)["cashier_max_discount"] or 10)
    mgr = _sess("ralph")
    # manager PUT succeeds (200) but the discount cap must NOT move
    r = mgr.put(SETTINGS, json={"cashier_max_discount": base + 7})
    assert r.status_code == 200, r.text
    assert float(_get(admin)["cashier_max_discount"] or 0) == base, "manager must not change discount caps"


# ---- admin: full control incl. discounts --------------------------------

def test_admin_can_change_discount_caps():
    s = _sess("felix")
    base = float(_get(s)["cashier_max_discount"] or 10)
    target = base + 3
    try:
        r = s.put(SETTINGS, json={"cashier_max_discount": target})
        assert r.status_code == 200, r.text
        assert float(_get(s)["cashier_max_discount"]) == target
    finally:
        s.put(SETTINGS, json={"cashier_max_discount": base})   # restore
