# File: src/tests/test_integrity_sweep.py
"""BL-100 #4 — the STANDING SEAL SWEEP (barcode integrity).

The lesson (CLAUDE.md, the MAX camper seals): when one seal fails, check ALL the seals. Two real
till incidents motivate this: the Tycoon Gas scan hit a DISCONTINUED dupe that still held the real
EAN ("discontinued" dead-end), and the GIZEH `42470335` code was double-assigned to both the Pink
and the Black rolls (an ambiguous scan). This sweep finds that class of cross-wire BEFORE a cashier
scans into one at the till — the most expensive place to discover a bad match.

`barcode_integrity_sweep` is read-only: it SURFACES findings for a human to confirm physically, it
never mutates. These tests reproduce both incidents in miniature and assert the sweep names them.
"""
import uuid

import pytest
from sqlalchemy import delete

from src.db.models import LineItemModel, ProductModel, ProductBarcodeModel
from src.routes.pos_router import barcode_integrity_sweep

_MGR = {"username": "ralph", "realm_access": {"roles": ["👔️ pos-manager"]}}


def _p(name, barcode=None, active=True, **kw):
    return ProductModel(sku=f"SEAL-{uuid.uuid4().hex[:8]}", name=name, price=1.0,
                        is_active=active, barcode=barcode, **kw)


async def _clear(db):
    # the shared in-memory DB doesn't drop cleanly between tests → clear first
    await db.execute(delete(LineItemModel))
    await db.execute(delete(ProductBarcodeModel))
    await db.execute(delete(ProductModel))


def _check(res, key):
    return next(c for c in res["checks"] if c["key"] == key)


@pytest.mark.asyncio
async def test_clean_shop_reports_no_crosswires(db_session):
    await _clear(db_session)
    db_session.add_all([
        _p("Clean A", barcode="4001122330011"),
        _p("Clean B", barcode="4001122330028"),
    ])
    await db_session.commit()
    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    assert res["clean"] is True
    assert res["total_findings"] == 0


@pytest.mark.asyncio
async def test_collision_primary_vs_alias_is_flagged(db_session):
    # the real GIZEH case: 42470335 is the PRIMARY of Pink and an ALIAS on Black
    await _clear(db_session)
    pink = _p("GIZEH All Pink Rolls Slim", barcode="42470335")
    black = _p("GIZEH Black Rolls Slim", barcode="42238072")
    db_session.add_all([pink, black])
    await db_session.commit()
    db_session.add(ProductBarcodeModel(product_id=black.id, barcode="42470335"))
    await db_session.commit()

    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    coll = _check(res, "collision")
    assert coll["count"] == 1
    f = coll["findings"][0]
    assert f["barcode"] == "42470335"
    roles = {(p["name"], p["role"]) for p in f["products"]}
    assert ("GIZEH All Pink Rolls Slim", "primary") in roles
    assert ("GIZEH Black Rolls Slim", "alias") in roles
    assert coll["severity"] == "high"


@pytest.mark.asyncio
async def test_same_products_primary_and_own_alias_not_flagged(db_session):
    # a code that is a product's primary AND also aliased on the SAME product is ONE product,
    # not a cross-wire — must not raise a false positive (count DISTINCT product, not rows)
    await _clear(db_session)
    p = _p("Self twin", barcode="4222333444055")
    db_session.add(p)
    await db_session.commit()
    db_session.add(ProductBarcodeModel(product_id=p.id, barcode="4222333444055"))
    await db_session.commit()
    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    assert _check(res, "collision")["count"] == 0


@pytest.mark.asyncio
async def test_stranded_barcode_on_discontinued_product(db_session):
    # the Tycoon failure mode: a dead row still owns a scan-live code, no active twin shares it
    await _clear(db_session)
    db_session.add_all([
        _p("Tycoon dupe (discontinued)", barcode="4035687900004", active=False),
        _p("Something Live", barcode="4001122330011"),
    ])
    await db_session.commit()
    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    stranded = _check(res, "stranded_inactive")
    assert stranded["count"] == 1
    assert stranded["findings"][0]["barcode"] == "4035687900004"
    assert stranded["severity"] == "medium"


@pytest.mark.asyncio
async def test_collision_not_double_counted_as_stranded(db_session):
    # a code that is a discontinued row's primary AND an active row's alias is a COLLISION
    # (Check A), NOT also counted as stranded (Check B) — no double-reporting
    await _clear(db_session)
    dead = _p("Dead twin", barcode="4111222333044", active=False)   # primary on inactive
    live = _p("Live twin", barcode="4111222555066", active=True)    # different primary
    db_session.add_all([dead, live])
    await db_session.commit()
    db_session.add(ProductBarcodeModel(product_id=live.id, barcode="4111222333044"))  # alias on live
    await db_session.commit()
    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    assert _check(res, "collision")["count"] == 1
    assert _check(res, "stranded_inactive")["count"] == 0


@pytest.mark.asyncio
async def test_blank_barcodes_never_flagged(db_session):
    # empty-string / null barcodes must not collide with each other
    await _clear(db_session)
    db_session.add_all([
        _p("No code A", barcode=None),
        _p("No code B", barcode=""),
        _p("No code C", barcode=None, active=False),
    ])
    await db_session.commit()
    res = await barcode_integrity_sweep(db=db_session, current_user=_MGR)
    assert res["clean"] is True
