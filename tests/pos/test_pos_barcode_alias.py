"""
Alias barcodes (BL-90) — "scan once, known forever" must hold even when a single
article carries more than one barcode (retail EAN + logistics/case code).

LOCKS: a product can be resolved by its primary barcode OR any attached alias;
attaching is idempotent for the same product and a 409 for a different one;
an unknown barcode is a clean 404.
"""
import uuid

import pytest

from conftest import POS, find_product


def _new_barcode():
    # Digits-only, unique per run, won't collide on the shared DB.
    return "99" + uuid.uuid4().int.__str__()[:11]


def _create_product(session, barcode):
    r = session.post(f"{POS}/products", json={
        "barcode": barcode,
        "sku": "ALIAS-TEST-" + barcode,
        "name": "Alias Test Item " + barcode,
        "price": "4.20",
        "stock_quantity": 9999,
    })
    assert r.status_code == 201, f"create failed: {r.status_code} {r.text[:200]}"
    return r.json()


def test_alias_barcode_resolves_to_same_product(session):
    """Attach a 2nd barcode -> looking it up returns the SAME product."""
    primary = _new_barcode()
    product = _create_product(session, primary)

    # Primary resolves.
    p = find_product(session, barcode=primary)
    assert p and p["id"] == product["id"]

    # Attach an alias.
    alias = _new_barcode()
    r = session.post(f"{POS}/products/{product['id']}/barcodes", json={"barcode": alias})
    assert r.status_code == 201, f"link failed: {r.status_code} {r.text[:200]}"
    assert r.json()["status"] == "linked"

    # Alias now resolves to the same product (THE fix).
    p2 = find_product(session, barcode=alias)
    assert p2, "alias barcode did not resolve -- scan-once-known-forever broken"
    assert p2["id"] == product["id"], "alias resolved to the WRONG product"


def test_unknown_barcode_is_404(session):
    """A never-seen barcode is a clean 404, not a 500."""
    r = session.get(f"{POS}/products/barcode/{_new_barcode()}")
    assert r.status_code == 404


def test_relinking_same_barcode_to_same_product_is_idempotent(session):
    """Linking a code the product already owns is a no-op, not an error."""
    primary = _new_barcode()
    product = _create_product(session, primary)
    # Its own primary barcode -> already linked, no duplicate, no 500.
    r = session.post(f"{POS}/products/{product['id']}/barcodes", json={"barcode": primary})
    assert r.status_code == 201
    assert r.json()["status"] == "already_linked"


def test_linking_a_used_barcode_to_another_product_is_409(session):
    """A barcode already owned by product A cannot be stolen by product B."""
    bc_a = _new_barcode()
    prod_a = _create_product(session, bc_a)
    prod_b = _create_product(session, _new_barcode())

    r = session.post(f"{POS}/products/{prod_b['id']}/barcodes", json={"barcode": bc_a})
    assert r.status_code == 409, f"expected 409, got {r.status_code} {r.text[:160]}"
