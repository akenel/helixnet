"""The Kiosk — public guest lookup (banco-kiosk-guest-station).

A customer walks up to the self-service station, scans a barcode, and gets a GUEST-SAFE
product view in their language. No auth. These lock two contracts: (1) it resolves an active
product by barcode and never 404s on a miss (kiosk shows a friendly 'ask staff'), and (2) it
never leaks cost / margin / supplier / stock to a guest.
"""
import uuid

import pytest

from src.db.models.product_model import ProductModel
from src.routes import pos_router


async def _make_product(db, *, barcode, active=True, price=14.90, cost=6.0):
    p = ProductModel(
        sku=f"KSK-{uuid.uuid4().hex[:8]}", name="CBD Gummies 10x", price=price,
        cost=cost, barcode=barcode, is_active=active, category="Edibles",
        supplier_name="SecretSupplier AG",
        description="Ten fruity CBD gummies.",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@pytest.mark.asyncio
async def test_kiosk_lookup_resolves_active_product(db_session):
    p = await _make_product(db_session, barcode="7610000123469")
    out = await pos_router.kiosk_lookup(barcode="7610000123469", lang="en", db=db_session)
    assert out["found"] is True
    assert out["id"] == str(p.id)
    assert out["price"] == "14.90"
    assert out["currency"] == "CHF"
    assert out["name"]


@pytest.mark.asyncio
async def test_kiosk_lookup_is_guest_safe(db_session):
    """A guest must never see cost / margin / supplier / stock through the kiosk."""
    await _make_product(db_session, barcode="7610000999999", cost=6.0)
    out = await pos_router.kiosk_lookup(barcode="7610000999999", lang="en", db=db_session)
    for leak in ("cost", "margin", "supplier", "supplier_name", "stock", "stock_quantity"):
        assert leak not in out, f"kiosk leaked '{leak}' to a guest"


@pytest.mark.asyncio
async def test_kiosk_lookup_miss_is_friendly_not_404(db_session):
    out = await pos_router.kiosk_lookup(barcode="0000nope", lang="en", db=db_session)
    assert out["found"] is False   # no HTTPException — the kiosk shows 'ask staff'


@pytest.mark.asyncio
async def test_kiosk_lookup_skips_inactive(db_session):
    await _make_product(db_session, barcode="7610000111111", active=False)
    out = await pos_router.kiosk_lookup(barcode="7610000111111", lang="en", db=db_session)
    assert out["found"] is False


@pytest.mark.asyncio
async def test_kiosk_lookup_blank_barcode(db_session):
    out = await pos_router.kiosk_lookup(barcode="", lang="en", db=db_session)
    assert out["found"] is False


@pytest.mark.asyncio
async def test_kiosk_view_by_id(db_session):
    """A guest who typed a NAME picks a search result → the kiosk opens it by id."""
    p = await _make_product(db_session, barcode="7610000222222")
    out = await pos_router.kiosk_view(product_id=str(p.id), lang="en", db=db_session)
    assert out["found"] is True
    assert out["id"] == str(p.id)
    for leak in ("cost", "supplier", "supplier_name", "stock_quantity"):
        assert leak not in out


@pytest.mark.asyncio
async def test_kiosk_view_inactive_or_bad_id(db_session):
    p = await _make_product(db_session, barcode="7610000333333", active=False)
    assert (await pos_router.kiosk_view(product_id=str(p.id), lang="en", db=db_session))["found"] is False
    assert (await pos_router.kiosk_view(product_id="not-a-uuid", lang="en", db=db_session))["found"] is False
    assert (await pos_router.kiosk_view(product_id="", lang="en", db=db_session))["found"] is False
