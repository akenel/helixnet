"""Age gate (18+) — the sale-path compliance hole is closed.

Black-box HTTP against the running server (same harness as the rest of tests/pos).
Proves the server REJECTS an age-restricted (18+) line unless age is cleared, and that
the back-compat rule never breaks an existing member or a non-restricted sale.

The 18+ truth is derived server-side from the product's `product_class` (alcohol /
tobacco / cbd_hemp), NOT from a client flag — so these tests create a real
`product_class='alcohol'` product via /products/quick and ring it through /sales.

Cases:
  1. memberless 18+ blocked WITHOUT age_verified            -> 400
  2. memberless 18+ allowed WITH age_verified               -> 201  (method=cashier_attest)
  3. under-18 member (DOB present, <18) blocked             -> 400  (DOB authoritative)
  4. 18+ member (DOB present, >=18) allowed                 -> 201  (method=member)
  5. legacy member (age_confirmed=True, NO birthdate)       -> 201  (back-compat)
  6. non-restricted sale, no member, no age_verified        -> 201  (gate stays silent)
  7. legacy 3-step /checkout path is guarded too            -> 400
  8. enroll accepts + round-trips `birthdate`; old enroll still works

Run (local):    source .venv/bin/activate && python -m pytest tests/pos/test_pos_age_gate.py -v
Run (sandbox):  ENV=sandbox POS_REALM=kc-sandbox python -m pytest tests/pos/test_pos_age_gate.py -v
"""
import uuid
from datetime import date

from conftest import POS, API_BASE

CUST = f"{API_BASE}/api/v1/customers"


# ---- helpers --------------------------------------------------------------

def _mk_product(session, product_class):
    """Create a throwaway product of the given class. `product_class` decides 18+
    (alcohol/tobacco/cbd_hemp = restricted; standard = not) — that's the source of truth."""
    stamp = uuid.uuid4().hex[:10]
    body = {
        "sku": f"AGE-{stamp}",
        "name": f"Age Gate Test {stamp}",
        "price": "9.90",
        "product_class": product_class,
        # Mirror how the catalog enricher stores it (display flag derived from class). The
        # SERVER gate reads product_class, not this — but keep the row self-consistent.
        "is_age_restricted": product_class in ("alcohol", "tobacco_nicotine", "cbd_hemp"),
        "category": "Age-Gate-Test",
    }
    r = session.post(f"{POS}/products/quick", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _age_product(session):
    p = _mk_product(session, "alcohol")
    assert p["is_age_restricted"] is True, p
    return p


def _std_product(session):
    p = _mk_product(session, "standard")
    assert p["is_age_restricted"] is False, p
    return p


def _sale_body(product_id, customer_id=None, age_verified=None, payment_method="twint"):
    body = {
        "client_uuid": str(uuid.uuid4()),
        "payment_method": payment_method,
        "lines": [{"product_id": product_id, "quantity": 1, "consumption": "takeaway"}],
    }
    if customer_id is not None:
        body["customer_id"] = customer_id
    if age_verified is not None:
        body["age_verified"] = age_verified
    return body


def _new_member(session, birthdate=None, age_confirmed=True):
    handle = "age_" + uuid.uuid4().hex[:8]
    payload = {"handle": handle, "age_confirmed": age_confirmed}
    if birthdate is not None:
        payload["birthdate"] = birthdate
    r = session.post(CUST, json=payload)
    r.raise_for_status()
    return r.json()["id"]


def _years_ago(n):
    t = date.today()
    # Use Jan 1 to stay well clear of the birthday boundary in both directions.
    return date(t.year - n, 1, 1).isoformat()


# ---- 1. memberless 18+ blocked without attestation ------------------------

def test_memberless_age_restricted_blocked_without_age_verified(session):
    p = _age_product(session)
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"]))
    assert r.status_code == 400, r.text
    low = r.text.lower()
    assert "18" in low or "age" in low or "verif" in low


# ---- 2. memberless 18+ allowed WITH attestation ---------------------------

def test_memberless_age_restricted_allowed_with_age_verified(session):
    p = _age_product(session)
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"], age_verified=True))
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"


# ---- 3. under-18 member blocked (DOB is authoritative) --------------------

def test_under_18_member_blocked(session):
    p = _age_product(session)
    cid = _new_member(session, birthdate=_years_ago(10))  # 10yo, but age_confirmed=True
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"], customer_id=cid))
    assert r.status_code == 400, r.text
    assert "18" in r.text or "under" in r.text.lower()


def test_under_18_member_blocked_even_with_age_verified(session):
    """A proven minor cannot be overridden by a cashier attestation."""
    p = _age_product(session)
    cid = _new_member(session, birthdate=_years_ago(10))
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"], customer_id=cid, age_verified=True))
    assert r.status_code == 400, r.text


# ---- 4. 18+ member allowed ------------------------------------------------

def test_of_age_member_allowed(session):
    p = _age_product(session)
    cid = _new_member(session, birthdate=_years_ago(30))
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"], customer_id=cid))
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"


# ---- 5. legacy member (no DOB, age_confirmed) allowed [BACK-COMPAT] -------

def test_legacy_member_no_dob_allowed(session):
    p = _age_product(session)
    cid = _new_member(session)  # age_confirmed=True, birthdate NULL — an existing member
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"], customer_id=cid))
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"


# ---- 6. non-restricted sale unaffected ------------------------------------

def test_non_restricted_sale_unaffected(session):
    p = _std_product(session)
    r = session.post(f"{POS}/sales", json=_sale_body(p["id"]))
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "completed"


# ---- 7. legacy 3-step /checkout path is guarded too -----------------------

def test_legacy_checkout_path_also_guarded(session):
    p = _age_product(session)
    tx = session.post(f"{POS}/transactions", json={})
    tx.raise_for_status()
    tx = tx.json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items",
                     json={"product_id": p["id"], "quantity": 1})
    r.raise_for_status()
    # No age clearance -> blocked
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={"payment_method": "twint"})
    assert r.status_code == 400, r.text
    # With attestation -> proceeds
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout",
                     json={"payment_method": "twint", "age_verified": True})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"


# ---- 8. enroll accepts + round-trips birthdate; old enroll still works ----

def test_enroll_accepts_birthdate_and_roundtrips(session):
    dob = _years_ago(25)
    cid = _new_member(session, birthdate=dob)
    r = session.get(f"{CUST}/{cid}")
    r.raise_for_status()
    assert r.json().get("birthdate") == dob


def test_enroll_without_birthdate_still_works(session):
    """The new nullable column must not make birthdate required (regression guard)."""
    handle = "nobd_" + uuid.uuid4().hex[:8]
    r = session.post(CUST, json={"handle": handle, "age_confirmed": True})
    assert r.status_code == 201, r.text
