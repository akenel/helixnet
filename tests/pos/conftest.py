"""
Shared fixtures for the Banco POS API regression suite.

Black-box HTTP tests: they hit the RUNNING server, they do NOT import the app
(so the host .venv is enough -- no fastapi needed). Auth is a REAL Keycloak
token via direct-access-grant (helix_pos_web is a public client with grants on).

Env model (matches docs/testing/POS-TESTING-SOP.md):
  ENV=local   (default) -> helix.local stack on this laptop
  ENV=staging           -> staging-banco.lapiazza.app on Hetzner

Run:
  source .venv/bin/activate
  python -m pytest tests/pos -v                 # local
  ENV=staging python -m pytest tests/pos -v     # staging
"""
import os
from decimal import Decimal

import pytest
import requests

requests.packages.urllib3.disable_warnings()

ENV = os.environ.get("ENV", "local").lower()

# (api_base, keycloak_base) per environment.
_ENVS = {
    "local": (
        os.environ.get("POS_API", "https://helix-platform.local"),
        os.environ.get("POS_KC", "https://keycloak.helix.local"),
    ),
    "staging": (
        os.environ.get("POS_API", "https://staging-banco.lapiazza.app"),
        os.environ.get("POS_KC", "https://lapiazza.app"),
    ),
}

API_BASE, KC_BASE = _ENVS[ENV]
REALM = os.environ.get("POS_REALM", "kc-pos-realm-dev")
CLIENT_ID = os.environ.get("POS_CLIENT", "helix_pos_web")
POS = f"{API_BASE}/api/v1/pos"
VAT_RATE = Decimal(os.environ.get("POS_VAT_RATE", "8.1"))


def _get_token(username: str, password: str = "helix_pass") -> str:
    """Mint a real Keycloak access token via direct access grant."""
    r = requests.post(
        f"{KC_BASE}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "client_id": CLIENT_ID,
            "username": username,
            "password": password,
            "grant_type": "password",
        },
        verify=False,
        timeout=15,
    )
    r.raise_for_status()
    tok = r.json().get("access_token")
    assert tok, f"no access_token for {username}: {r.text[:200]}"
    return tok


def inclusive_vat(gross) -> Decimal:
    """The contained VAT inside a Swiss VAT-inclusive gross price.
    Mirrors the server's _inclusive_vat() and the client calculateVAT()."""
    g = Decimal(str(gross))
    return (g * VAT_RATE / (Decimal("100") + VAT_RATE)).quantize(Decimal("0.01"))


@pytest.fixture(scope="session")
def env_info():
    return {"env": ENV, "api": API_BASE, "kc": KC_BASE, "realm": REALM}


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_products(cashier_token):
    """Teardown hygiene: the suite creates throwaway TEST- products (refund, o2c,
    procure-to-pay). The DB is SHARED, so deactivate them after the run instead of
    leaving thousands of junk rows that crowd out the seeded catalogue. DELETE soft-
    deactivates (is_active=False), so they vanish from the active listing."""
    yield
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {cashier_token}"})
    s.verify = False
    skip = 0
    while True:
        try:
            batch = s.get(f"{POS}/products", params={"limit": 500, "skip": skip}, timeout=20).json()
        except Exception:
            return
        if not batch:
            return
        for p in batch:
            if (p.get("sku") or "").startswith("TEST-"):
                try:
                    s.delete(f"{POS}/products/{p['id']}", timeout=15)
                except Exception:
                    pass
        if len(batch) < 500:
            return
        skip += 500


@pytest.fixture(scope="session")
def cashier_token():
    """Felix is admin (all POS roles); use him as the authenticated cashier."""
    return _get_token("felix")


@pytest.fixture
def session(cashier_token):
    """A requests.Session pre-loaded with the bearer token + verify off."""
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {cashier_token}"})
    s.verify = False
    s.request = _timeout_wrapper(s.request)
    return s


def _timeout_wrapper(fn):
    def wrapped(method, url, **kw):
        kw.setdefault("timeout", 15)
        return fn(method, url, **kw)
    return wrapped


# ---- small API helpers shared across tests -------------------------------

def list_products(session):
    r = session.get(f"{POS}/products", params={"limit": 100})
    r.raise_for_status()
    return r.json()


def find_product(session, sku=None, barcode=None):
    """Robust lookup that does NOT depend on a 100-row listing window (the shared DB
    holds thousands of products). Barcode = a direct scan endpoint; SKU = paged scan."""
    if barcode:
        r = session.get(f"{POS}/products/barcode/{barcode}")
        return r.json() if r.status_code == 200 else None
    skip = 0
    while sku:
        batch = session.get(f"{POS}/products", params={"limit": 500, "skip": skip}).json()
        if not batch:
            return None
        for p in batch:
            if p.get("sku") == sku:
                return p
        if len(batch) < 500:
            return None
        skip += 500
    return None


def ring_sale(session, items, payment_method="cash", amount_tendered=None, department=None):
    """items = [(product_id, qty, unit_price), ...]. Returns the completed transaction dict.
    Creates a transaction, adds line items, checks out.
    department (optional): 'head_shop' | 'cafe' | 'grow_supplies' -- which counter rang it."""
    open_payload = {} if department is None else {"department": department}
    tx = session.post(f"{POS}/transactions", json=open_payload)
    tx.raise_for_status()
    tx = tx.json()
    for product_id, qty, unit_price in items:
        r = session.post(
            f"{POS}/transactions/{tx['id']}/items",
            json={
                "product_id": product_id,
                "quantity": qty,
                "unit_price": str(unit_price),
                "discount_percent": "0",
            },
        )
        r.raise_for_status()
    payload = {"payment_method": payment_method}
    if amount_tendered is not None:
        payload["amount_tendered"] = str(amount_tendered)
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json=payload)
    r.raise_for_status()
    return r.json()


def get_transaction(session, tx_id):
    r = session.get(f"{POS}/transactions/{tx_id}")
    r.raise_for_status()
    return r.json()
