"""Mass cleanup for the Catalog Cockpit — bulk delete / discontinue with the sold-guard.

Angel's Cockpit fills with junk during a migration (test rows, ALIAS dupes, mis-scans).
He wanted to nuke them a batch at a time OR one at a time. The one rule that can't bend:
a product that has EVER sold must never be hard-deleted — that would orphan its line_items
and blow a hole in receipts / 10-year retention. These lock that contract at the route layer.
"""
import uuid

import pytest

from sqlalchemy import select

from src.db.models.product_model import ProductModel
from src.routes import pos_router


async def _make_product(db, name="TEST junk row") -> ProductModel:
    p = ProductModel(sku=f"TEST-{uuid.uuid4().hex[:8]}", name=name, price=1.0)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


_USER = {"username": "ralph", "roles": ["pos-manager"]}


@pytest.mark.asyncio
async def test_bulk_permanent_deletes_never_sold(db_session):
    a = await _make_product(db_session)
    b = await _make_product(db_session)
    res = await pos_router.bulk_delete_products(
        {"product_ids": [str(a.id), str(b.id)], "action": "permanent"},
        db=db_session, current_user=_USER,
    )
    assert set(res["deleted"]) == {str(a.id), str(b.id)}
    assert res["skipped_sold"] == []
    gone = (await db_session.execute(
        select(ProductModel).where(ProductModel.id.in_([a.id, b.id])))).scalars().all()
    assert gone == []


@pytest.mark.asyncio
async def test_bulk_discontinue_keeps_the_row(db_session):
    p = await _make_product(db_session)
    res = await pos_router.bulk_delete_products(
        {"product_ids": [str(p.id)], "action": "discontinue"},
        db=db_session, current_user=_USER,
    )
    assert res["discontinued"] == [str(p.id)]
    assert res["deleted"] == []
    await db_session.refresh(p)
    assert p.is_active is False   # soft — history survives


@pytest.mark.asyncio
async def test_bulk_permanent_refuses_a_sold_product(db_session, monkeypatch):
    """The guardrail: a sold product is REPORTED (skipped_sold), never erased — even in a
    batch alongside deletable junk. The junk still goes; the sold one stays."""
    sold = await _make_product(db_session, name="Coca-Cola (has sold)")
    junk = await _make_product(db_session, name="mis-scan dupe")

    async def _fake_count(db, pid):
        return 5 if str(pid) == str(sold.id) else 0
    monkeypatch.setattr(pos_router, "_product_sales_count", _fake_count)

    res = await pos_router.bulk_delete_products(
        {"product_ids": [str(sold.id), str(junk.id)], "action": "permanent"},
        db=db_session, current_user=_USER,
    )
    assert res["deleted"] == [str(junk.id)]
    assert len(res["skipped_sold"]) == 1
    assert res["skipped_sold"][0]["id"] == str(sold.id)
    assert res["skipped_sold"][0]["sales"] == 5
    # The sold product is untouched and still active.
    await db_session.refresh(sold)
    assert sold.is_active is True


@pytest.mark.asyncio
async def test_bulk_empty_list_rejected(db_session):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as ei:
        await pos_router.bulk_delete_products(
            {"product_ids": [], "action": "permanent"}, db=db_session, current_user=_USER)
    assert ei.value.status_code == 400
