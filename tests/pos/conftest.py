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
    # ENV=sandbox POS_REALM=kc-sandbox -> the box sandbox tree (deploy-banco.py sandbox).
    "sandbox": (
        os.environ.get("POS_API", "https://sandbox-banco.lapiazza.app"),
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


@pytest.fixture(autouse=True)
def _ensure_open_drawer(request):
    """A cash sale now requires an open cash drawer (guard shipped in 9617589). Most POS
    tests ring cash without opening one, so ensure felix has a drawer open before each test.
    test_pos_cash_shift owns its drawer lifecycle (and tests the guard's window semantics),
    so it's skipped here. Left open between tests on purpose — the next test reuses it."""
    if "test_pos_cash_shift" in request.node.nodeid:
        yield
        return
    s = request.getfixturevalue("session")
    try:
        cur = s.get(f"{POS}/shift/current").json()
    except Exception:
        cur = {}
    if not cur.get("open"):
        s.post(f"{POS}/shift/open", json={"opening_float": "100.00"})
    yield


# ---- small API helpers shared across tests -------------------------------

def list_products(session):
    r = session.get(f"{POS}/products", params={"limit": 100})
    r.raise_for_status()
    return r.json()


def find_product(session, sku=None, barcode=None):
    # Use EXACT, indexed lookups instead of paging the (now ~7k-row) catalog —
    # the old list(limit=100) scan flaked when a seeded product fell off page 1.
    if barcode:
        r = session.get(f"{POS}/products/barcode/{barcode}")
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        r.raise_for_status()
    if sku:
        r = session.get(f"{POS}/search", params={"q": sku, "limit": 50})
        r.raise_for_status()
        for p in r.json().get("items", []):
            if p.get("sku") == sku:
                return p
    return None


def ring_sale(session, items, payment_method="cash", amount_tendered=None):
    """items = [(product_id, qty, unit_price), ...]. Returns the completed transaction dict.
    Creates a transaction, adds line items, checks out."""
    tx = session.post(f"{POS}/transactions", json={})
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
