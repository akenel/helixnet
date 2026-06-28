"""Input guards found by the monkey/fuzz pass (2026-06-27).

Black-box: hit the running server like the rest of tests/pos.
"""
from conftest import POS


def _open_drawer(session):
    if not session.get(f"{POS}/shift/current").json().get("open"):
        session.post(f"{POS}/shift/open", json={"opening_float": "100.00"})


def test_empty_cart_checkout_is_blocked(session):
    """A transaction with no line items must NOT complete (was a CHF 0 phantom sale)."""
    _open_drawer(session)
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/checkout", json={"payment_method": "twint"})
    assert r.status_code == 400, r.text
    assert "empty" in r.text.lower()


def _find_by_class(session, classes):
    items = session.get(f"{POS}/search", params={"q": "", "limit": 300}).json().get("items", [])
    return next((p for p in items if p.get("product_class") in classes), None)


def test_discount_blocked_on_promo_restricted_class(session):
    """Tobacco/alcohol are promotion-restricted by law (Tabakproduktegesetz/Alkoholgesetz)
    — a discount on those lines must be rejected, for cashier AND manager. (Angel: Pam
    discounted cigarettes; the role cap alone let it through.)"""
    import pytest
    _open_drawer(session)
    prod = _find_by_class(session, ("tobacco_nicotine", "alcohol"))
    if not prod:
        pytest.skip("no tobacco/alcohol product seeded")
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items",
                     json={"product_id": prod["id"], "quantity": 1, "discount_percent": 10})
    assert r.status_code == 400, r.text
    assert "restricted" in r.text.lower()


def test_discount_still_works_on_standard_goods(session):
    """The block is class-scoped — a normal item still discounts fine."""
    import pytest
    _open_drawer(session)
    prod = _find_by_class(session, (None, "standard"))
    if not prod:
        pytest.skip("no standard product")
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items",
                     json={"product_id": prod["id"], "quantity": 1, "discount_percent": 10})
    assert r.status_code == 200, r.text


def test_line_quantity_is_capped(session):
    """A fat-finger 10,000,000 quantity must be rejected (cap = 10000)."""
    # find any product
    p = session.get(f"{POS}/products", params={"limit": 1}).json()
    if not p:
        return  # empty catalog env — nothing to add
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items",
                     json={"product_id": p[0]["id"], "quantity": 10_000_000})
    assert r.status_code == 422, r.text


def test_normal_quantity_still_works(session):
    """The cap must not block legitimate quantities."""
    p = session.get(f"{POS}/products", params={"limit": 1}).json()
    if not p:
        return
    tx = session.post(f"{POS}/transactions", json={}).json()
    r = session.post(f"{POS}/transactions/{tx['id']}/items",
                     json={"product_id": p[0]["id"], "quantity": 12})
    assert r.status_code in (200, 201), r.text
