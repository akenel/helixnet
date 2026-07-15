"""The Kiosk member hook — public self-signup + first-order discount (banco-kiosk-guest-station).

A guest becomes a member right at the kiosk (10%) or on their own phone (15%) and earns a
one-time first-order discount. 18+ is required (head shop). Handle must be unique. These lock:
the discount-by-channel rule, the age gate, uniqueness, and that a scannable HLX- card is minted.
"""
import pytest

from fastapi import HTTPException
from sqlalchemy import select

from src.db.models.customer_model import CustomerModel
from src.routes import pos_router


def _body(**kw):
    base = dict(handle="stoner_sam", age_confirmed=True, source="kiosk", language="en")
    base.update(kw)
    return pos_router.KioskSignup(**base)


@pytest.mark.asyncio
async def test_signup_kiosk_gives_10(db_session):
    out = await pos_router.kiosk_signup(_body(handle="kiosk_kid"), db=db_session)
    assert out["ok"] is True
    assert out["discount_pct"] == 10
    assert out["source"] == "kiosk"
    assert out["qr_code"].startswith("HLX-")     # scannable at the till
    row = (await db_session.execute(
        select(CustomerModel).where(CustomerModel.handle == "kiosk_kid"))).scalar_one()
    assert row.welcome_discount_pct == 10
    assert row.welcome_discount_used is False
    assert row.age_confirmed is True


@pytest.mark.asyncio
async def test_signup_phone_gives_15(db_session):
    out = await pos_router.kiosk_signup(_body(handle="phone_phil", source="phone"), db=db_session)
    assert out["discount_pct"] == 15
    assert out["source"] == "phone"


@pytest.mark.asyncio
async def test_signup_requires_18(db_session):
    with pytest.raises(HTTPException) as ei:
        await pos_router.kiosk_signup(_body(handle="too_young", age_confirmed=False), db=db_session)
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_signup_handle_must_be_unique(db_session):
    await pos_router.kiosk_signup(_body(handle="dupe_dan"), db=db_session)
    with pytest.raises(HTTPException) as ei:
        await pos_router.kiosk_signup(_body(handle="Dupe_Dan"), db=db_session)   # case-insensitive
    assert ei.value.status_code == 409


@pytest.mark.asyncio
async def test_signup_rejects_bad_handle(db_session):
    for bad in ("ab", "no spaces here", "a" * 40, "bad!char"):
        with pytest.raises(HTTPException) as ei:
            await pos_router.kiosk_signup(_body(handle=bad), db=db_session)
        assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_new_today_lists_the_signup(db_session):
    await pos_router.kiosk_signup(_body(handle="today_tom", source="phone"), db=db_session)
    out = await pos_router.customers_new_today(db=db_session, current_user={"username": "ralph"})
    handles = [m["handle"] for m in out["members"]]
    assert "today_tom" in handles
    tom = next(m for m in out["members"] if m["handle"] == "today_tom")
    assert tom["source"] == "phone"
    assert tom["welcome_discount_pct"] == 15
