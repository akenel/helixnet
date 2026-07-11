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

BL-98 — the BENCH mode (?mode=bench) on the same endpoint: the migration workbench.
Where mode=sold is REACTIVE (only what sold), mode=bench is PROACTIVE (every unfinished
product, sold or not) and gates on FOUR gaps — photo, description, category, cost:

  7. an UNSOLD half-baked product DOES appear on the bench (the sold/bench distinction)
  8. bench reports a done/total/remaining counter, and total >= remaining
  9. description + photo are real gaps on the bench (they are not gates in sold mode)
 10. filling category + cost alone does NOT clear a bench item (description/photo still open)
 11. the batch is limited and pageable (limit/offset)
 12. the shelf filter (?category=) only returns that category
 13. bench is manager-gated too (cashier pam -> 403)
"""
import uuid

from conftest import POS, _get_token, _timeout_wrapper
import requests

CLEANUP = f"{POS}/catalog/cleanup-queue"
BENCH = f"{CLEANUP}?mode=bench"


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


# ===========================================================================
# BL-98 — THE BENCH (mode=bench): the migration workbench
# ===========================================================================

def _bench(session, **params):
    """Fetch the bench. Returns the whole payload (we assert on the counter too)."""
    r = session.get(CLEANUP, params={"mode": "bench", **params})
    assert r.status_code == 200, r.text
    return r.json()


def _shelf():
    """A category no other product uses. The bench is a PAGED view over the whole catalog
    (a real DB has hundreds of unfinished items and `limit` caps at 100), so a test must
    isolate its own shelf to find its item deterministically — never assume page 1."""
    return f"Shelf{uuid.uuid4().hex[:8]}"


def _on_bench(session, shelf, pid):
    """Find pid on its own shelf (scoped, so global DB state can't hide it)."""
    return _find(_bench(session, category=shelf, limit=100)["items"], pid)


# ---- 7: the sold/bench distinction — UNSOLD unfinished IS on the bench ----

def test_unsold_unfinished_product_appears_on_the_bench(session):
    """The whole point of BL-98: mode=sold only ever shows what SOLD (test 4 proves an
    unsold item stays hidden there). The bench is PROACTIVE — it shows the item precisely
    because the migration is about products nobody has rung up yet."""
    shelf = _shelf()
    p = _mk_otf(session, category=shelf)        # unfinished (no cost/desc/photo), never sold
    assert _find(_queue(session), p["id"]) is None          # ...invisible to mode=sold
    assert _on_bench(session, shelf, p["id"]) is not None   # ...but ON the bench


# ---- 8: the counter that replaces the paper binder ------------------------

def test_bench_reports_progress_counter(session):
    _mk_otf(session)                            # guarantee at least one unfinished item
    data = _bench(session)
    assert data["mode"] == "bench"
    for k in ("done", "total", "remaining"):
        assert isinstance(data[k], int), f"{k} must be an int"
    assert data["total"] >= data["remaining"] >= 1
    # done/total/remaining must be internally consistent — the counter can't lie.
    assert data["done"] == data["total"] - data["remaining"]


# ---- 9: description + photo are REAL gaps on the bench --------------------

def test_bench_gates_on_description_and_photo(session):
    shelf = _shelf()
    p = _mk_otf(session, category=shelf, cost=2.00)   # category+cost filled...
    # ...so mode=sold would consider it complete, but the bench still wants desc + photo.
    row = _on_bench(session, shelf, p["id"])
    assert row is not None, "a product with no description/photo must stay on the bench"
    assert row["gaps"]["description"] is True
    assert row["gaps"]["photo"] is True
    assert row["gaps"]["category"] is False
    assert row["gaps"]["cost"] is False


# ---- 10: category+cost alone does NOT clear a bench item ------------------

def test_bench_item_needs_all_four_gaps_filled(session):
    shelf = _shelf()
    p = _mk_otf(session)                        # no category, no cost, no desc, no photo
    r = session.put(f"{POS}/products/{p['id']}", json={"category": shelf, "cost": 1.25})
    assert r.status_code == 200, r.text
    # Those two would have cleared mode=sold (test 2). The bench holds it — desc/photo open.
    row = _on_bench(session, shelf, p["id"])
    assert row is not None, "category+cost alone must NOT clear the bench"
    assert row["gaps"]["description"] is True
    assert row["gaps"]["photo"] is True

    # Adding a description closes that gap but the photo still holds it on the bench.
    r = session.put(f"{POS}/products/{p['id']}", json={"description": "A pack of papers."})
    assert r.status_code == 200, r.text
    row = _on_bench(session, shelf, p["id"])
    assert row is not None, "still no photo -> still on the bench"
    assert row["gaps"]["description"] is False
    assert row["gaps"]["photo"] is True


# ---- 11: the batch is limited + pageable ---------------------------------

def test_bench_batch_is_limited_and_pageable(session):
    for _ in range(3):
        _mk_otf(session)                        # ensure there's more than one page of work

    first = _bench(session, limit=2, offset=0)
    assert len(first["items"]) <= 2, "limit must cap the batch"
    assert first["limit"] == 2 and first["offset"] == 0

    second = _bench(session, limit=2, offset=2)
    assert second["offset"] == 2
    # Different page => different products (no overlap between batches).
    ids_a = {i["product_id"] for i in first["items"]}
    ids_b = {i["product_id"] for i in second["items"]}
    assert not (ids_a & ids_b), "offset must advance the batch, not repeat it"


# ---- 12: the shelf filter -------------------------------------------------

def test_bench_shelf_filter_returns_only_that_category(session):
    shelf = f"Shelf{uuid.uuid4().hex[:6]}"      # a category nothing else uses
    p = _mk_otf(session, category=shelf)        # no cost/desc/photo -> unfinished
    _mk_otf(session, category="Merch")          # a different shelf

    data = _bench(session, category=shelf, limit=100)
    assert data["items"], "the shelf must return its own unfinished items"
    assert all(i["category"] == shelf for i in data["items"]), "shelf filter must not leak other categories"
    assert _find(data["items"], p["id"]) is not None
    # The counter is scoped to the shelf too — you can finish ONE shelf and see it hit 100%.
    assert data["total"] >= 1


# ---- 13: bench is manager-gated too --------------------------------------

def test_bench_is_manager_gated():
    pam = requests.Session()
    pam.headers.update({"Authorization": f"Bearer {_get_token('pam')}"})
    pam.verify = False
    pam.request = _timeout_wrapper(pam.request)
    r = pam.get(CLEANUP, params={"mode": "bench"})
    assert r.status_code == 403, r.text
