"""The Kiosk guest cart / held orders (banco-kiosk-guest-station v2 Block 2a).

A guest builds a basket at the kiosk → gets a short CODE → the cashier's board shows it → Felix
rings it and taps done. These lock: server-authoritative pricing (client price is never trusted),
the member welcome-discount riding along, the open-board listing, and claim clearing it.
"""
import uuid

import pytest

from fastapi import HTTPException

from src.db.models.product_model import ProductModel
from src.db.models.customer_model import CustomerModel
from src.routes import pos_router


async def _product(db, price=10.0, name="Grinder"):
    p = ProductModel(sku=f"KC-{uuid.uuid4().hex[:8]}", name=name, price=price, is_active=True)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


def _upsert(items, **kw):
    return pos_router.KioskCartUpsert(
        items=[pos_router.KioskCartItem(product_id=str(pid), qty=q) for pid, q in items], **kw)


_USER = {"username": "pam", "roles": ["pos-cashier"]}


@pytest.mark.asyncio
async def test_cart_upsert_prices_from_catalog_not_client(db_session):
    a = await _product(db_session, price=10.0)
    b = await _product(db_session, price=4.50)
    out = await pos_router.kiosk_cart_upsert(_upsert([(a.id, 2), (b.id, 1)]), db=db_session)
    assert out["found"] is True
    assert len(out["code"]) >= 4
    assert out["item_count"] == 3
    assert out["total"] == "24.50"            # 2×10 + 1×4.50 — server-priced
    assert out["discount_pct"] == 0           # no member attached


@pytest.mark.asyncio
async def test_cart_get_by_code(db_session):
    a = await _product(db_session, price=7.0)
    made = await pos_router.kiosk_cart_upsert(_upsert([(a.id, 3)]), db=db_session)
    got = await pos_router.kiosk_cart_get(code=made["code"].lower(), db=db_session)   # case-insensitive
    assert got["found"] is True
    assert got["total"] == "21.00"
    miss = await pos_router.kiosk_cart_get(code="ZZZZ", db=db_session)
    assert miss["found"] is False


@pytest.mark.asyncio
async def test_cart_member_discount_rides_along(db_session):
    a = await _product(db_session, price=20.0)
    member = CustomerModel(handle="disco_dan", welcome_discount_pct=15,
                           welcome_discount_used=False, age_confirmed=True)
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    out = await pos_router.kiosk_cart_upsert(
        _upsert([(a.id, 1)], customer_id=str(member.id), source="phone"), db=db_session)
    assert out["member_handle"] == "disco_dan"
    assert out["discount_pct"] == 15
    assert out["discount_amount"] == "3.00"
    assert out["total_after"] == "17.00"


@pytest.mark.asyncio
async def test_open_board_and_claim(db_session):
    a = await _product(db_session, price=5.0)
    made = await pos_router.kiosk_cart_upsert(_upsert([(a.id, 2)]), db=db_session)
    code = made["code"]
    board = await pos_router.carts_open(db=db_session, current_user=_USER)
    assert code in [c["code"] for c in board["carts"]]
    # claim it → gone from the board
    claimed = await pos_router.cart_claim(code=code, db=db_session, current_user=_USER)
    assert claimed["status"] == "claimed"
    board2 = await pos_router.carts_open(db=db_session, current_user=_USER)
    assert code not in [c["code"] for c in board2["carts"]]


@pytest.mark.asyncio
async def test_empty_cart_not_on_board(db_session):
    made = await pos_router.kiosk_cart_upsert(_upsert([]), db=db_session)   # no items
    board = await pos_router.carts_open(db=db_session, current_user=_USER)
    assert made["code"] not in [c["code"] for c in board["carts"]]


@pytest.mark.asyncio
async def test_upsert_same_code_replaces_items(db_session):
    a = await _product(db_session, price=10.0)
    first = await pos_router.kiosk_cart_upsert(_upsert([(a.id, 1)]), db=db_session)
    second = await pos_router.kiosk_cart_upsert(_upsert([(a.id, 5)], code=first["code"]), db=db_session)
    assert second["code"] == first["code"]
    assert second["item_count"] == 5          # replaced, not appended
