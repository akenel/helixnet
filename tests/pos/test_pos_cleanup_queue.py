"""Sold-but-not-set-up cleanup cockpit (field-report item #3).

Black-box HTTP: a cashier's lean quick-add can leave a product half-baked (placeholder
category, no cost). Once it SELLS, it must surface in the manager cleanup queue and drop
off only when the gaps are filled — so nothing rung in a rush falls through permanently.

  1. a sold, half-baked product appears in the queue with its gaps
  2. filling category + cost (PUT) drops it off the queue
  3. a fully-set-up sold product never appears
  4. an UNSOLD half-baked product never appears (queue = SOLD only)
  5. queue is manager-gated (cashier pam -> 403)
  6. flipping 18+ via PUT reconciles product_class (gate reads class, not the column)
"""
import uuid

from conftest import POS, _get_token, _timeout_wrapper
import requests

CLEANUP = f"{POS}/catalog/cleanup-queue"


def _mk_otf(session, *, category=None, cost=None, price="4.00"):
    """A quick-add product. Omit category -> server files it under 'On the fly' (half-baked)."""
    stamp = uuid.uuid4().hex[:10]
    body = {"sku": f"CLN-{stamp}", "name": f"Cleanup Test {stamp}", "price": price}
    if category is not None:
        body["category"] = category
    if cost is not None:
        body["cost"] = cost
    r = session.post(f"{POS}/products/quick", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _sell(session, product_id, payment_method="twint"):
    body = {
        "client_uuid": str(uuid.uuid4()),
        "payment_method": payment_method,
        "lines": [{"product_id": product_id, "quantity": 1}],
    }
    r = session.post(f"{POS}/sales", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _queue(session):
    r = session.get(CLEANUP)
    assert r.status_code == 200, r.text
    return r.json()["items"]


def _find(items, pid):
    return next((x for x in items if x["product_id"] == pid), None)


# ---- 1 + 2: appears half-baked, drops off when fixed ----------------------

def test_sold_halfbaked_product_appears_then_clears(session):
    p = _mk_otf(session)                       # no category (-> "On the fly"), no cost
    _sell(session, p["id"])

    row = _find(_queue(session), p["id"])
    assert row is not None, "sold half-baked product must be in the queue"
    assert row["gaps"]["category"] is True
    assert row["gaps"]["cost"] is True
    assert row["qty_sold"] >= 1

    # Manager fills the two gaps
    r = session.put(f"{POS}/products/{p['id']}", json={"category": "Papers & Filters", "cost": 1.25})
    assert r.status_code == 200, r.text

    assert _find(_queue(session), p["id"]) is None, "fully set-up product must drop off the queue"


# ---- 3: a complete sold product never shows -------------------------------

def test_complete_sold_product_not_in_queue(session):
    p = _mk_otf(session, category="Papers & Filters", cost=1.00)
    _sell(session, p["id"])
    assert _find(_queue(session), p["id"]) is None


# ---- 4: unsold half-baked never shows (queue = SOLD only) -----------------

def test_unsold_halfbaked_product_not_in_queue(session):
    p = _mk_otf(session)                       # half-baked but never sold
    assert _find(_queue(session), p["id"]) is None


# ---- 5: manager-gated ------------------------------------------------------

def test_cleanup_queue_is_manager_gated():
    pam = requests.Session()
    pam.headers.update({"Authorization": f"Bearer {_get_token('pam')}"})
    pam.verify = False
    pam.request = _timeout_wrapper(pam.request)
    r = pam.get(CLEANUP)
    assert r.status_code == 403, r.text


# ---- 6: 18+ via PUT reconciles the class (the checkout-gate seal) ----------

def test_put_18plus_reconciles_product_class(session):
    p = _mk_otf(session, category="Merch", cost=2.00)   # standard class
    r = session.put(f"{POS}/products/{p['id']}", json={"is_age_restricted": True})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_age_restricted"] is True
    assert body["product_class"] == "age_restricted"    # the gating class, not a bare column flag
