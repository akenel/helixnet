# File: src/tests/test_bench_gap_filter.py
"""BL-98 gap FILTER — narrow the enrichment bench to ONE missing thing.

Angel, working the bench: "most are just cost — can we filter when a photo/description is
missing?" This locks that: `_bench_queue(gap='photo')` returns only the photo-gap items, the
per-gap `gap_counts` chips match, and an unknown gap falls back to the full four-gap bench.
"""
import uuid
from decimal import Decimal

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import delete

from src.db.models import LineItemModel, ProductModel
from src.routes.pos_router import _bench_queue, _readiness


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


# ---- Rookie workbench: readiness score, date scope, "keep tabs" notes ----

def test_readiness_flags_lazy_done():
    # cost + category + photo present but a 3-char description → NOT really done
    weak = ProductModel(sku="rk1", name="Bong XL", price=1.0, category="Pipes & Bongs",
                        cost=Decimal("1"), image_url="http://x/i.jpg", description="big")
    score, gripes = _readiness(weak)
    assert "description" in gripes and score < 100
    # a proper record scores 100 with no gripes
    good = ProductModel(sku="rk2", name="Bong XL", price=1.0, category="Pipes & Bongs",
                        cost=Decimal("1"), image_url="http://x/i.jpg",
                        description="A sturdy 40cm glass beaker bong with ice notches and a diffuser downstem.")
    assert _readiness(good) == (100, [])


def test_readiness_flags_unsorted_category():
    p = ProductModel(sku="rk3", name="Thing", price=1.0, category="Unsorted",
                     cost=Decimal("1"), image_url="http://x/i.jpg",
                     description="A decent, long-enough description of the thing right here.")
    _, gripes = _readiness(p)
    assert "category" in gripes


@pytest.mark.asyncio
async def test_period_yesterday_scopes_by_created_at(db_session):
    await db_session.execute(delete(LineItemModel))
    await db_session.execute(delete(ProductModel))
    now = datetime.now(timezone.utc)
    db_session.add(_p("Yday", created_at=(now - timedelta(days=1)).replace(hour=12)))
    db_session.add(_p("Old",  created_at=(now - timedelta(days=10))))
    await db_session.commit()
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, period="yesterday")
    names = {i["name"] for i in r["items"]}
    assert "Yday" in names and "Old" not in names
    assert r["period"] == "yesterday"


@pytest.mark.asyncio
async def test_noted_filter_and_work_note_roundtrip(db_session):
    await db_session.execute(delete(LineItemModel))
    await db_session.execute(delete(ProductModel))
    db_session.add(_p("HasNote", work_note="no cost yet — need the delivery slip"))
    db_session.add(_p("NoNote"))
    await db_session.commit()
    r = await _bench_queue(db_session, limit=20, offset=0, category=None, noted=True)
    assert {i["name"] for i in r["items"]} == {"HasNote"}
    assert r["items"][0]["work_note"] == "no cost yet — need the delivery slip"
    assert r["gap_counts"]["noted"] == 1
