# File: src/tests/test_bench_gap_filter.py
"""BL-98 gap FILTER — narrow the enrichment bench to ONE missing thing.

Angel, working the bench: "most are just cost — can we filter when a photo/description is
missing?" This locks that: `_bench_queue(gap='photo')` returns only the photo-gap items, the
per-gap `gap_counts` chips match, and an unknown gap falls back to the full four-gap bench.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete

from src.db.models import LineItemModel, ProductModel
from src.routes.pos_router import _bench_queue


def _p(name, **kw):
    return ProductModel(sku=f"BGAP-{uuid.uuid4().hex[:8]}", name=name, price=1.0,
                        is_active=True, **kw)


async def _seed(db):
    # the shared in-memory DB doesn't drop cleanly between tests → clear products first
    await db.execute(delete(LineItemModel))
    await db.execute(delete(ProductModel))
    IMG, TXT, CAT, COST = "http://x/i.jpg", "a description", "Bongs", Decimal("1.00")
    db.add_all([
        _p("Complete", image_url=IMG,  description=TXT, category=CAT, cost=COST),   # not on bench
        _p("NoPhoto",  image_url=None, description=TXT, category=CAT, cost=COST),   # photo gap only
        _p("NoDesc",   image_url=IMG,  description=None, category=CAT, cost=COST),  # description gap
        _p("NoCat",    image_url=IMG,  description=TXT, category=None, cost=COST),  # category gap
        _p("NoCost",   image_url=IMG,  description=TXT, category=CAT, cost=None),   # cost gap
    ])
    await db.commit()


@pytest.mark.asyncio
async def test_gap_photo_returns_only_photo_gaps(db_session):
    await _seed(db_session)
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, gap="photo")
    assert {i["name"] for i in r["items"]} == {"NoPhoto"}
    assert r["gap"] == "photo"
    assert r["remaining"] == 1          # done/total now reads "photos"


@pytest.mark.asyncio
async def test_gap_cost_returns_only_cost_gaps(db_session):
    await _seed(db_session)
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, gap="cost")
    assert {i["name"] for i in r["items"]} == {"NoCost"}


@pytest.mark.asyncio
async def test_gap_counts_are_per_kind(db_session):
    await _seed(db_session)
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, gap=None)
    gc = r["gap_counts"]
    assert gc["photo"] == 1 and gc["description"] == 1
    assert gc["category"] == 1 and gc["cost"] == 1
    assert gc["all"] == 4               # four distinct unfinished products
    assert r["total"] == 5              # five active products
    assert r["remaining"] == 4          # the whole bench


@pytest.mark.asyncio
async def test_unknown_gap_falls_back_to_all(db_session):
    await _seed(db_session)
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, gap="bogus")
    assert r["gap"] == "all"
    assert r["remaining"] == 4
