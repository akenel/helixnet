"""Postcard store footer — flatten store_settings into the card's 'come get it' footer.

The footer is the CLOSE: it turns every shared maker card into foot traffic back to the
counter, built from the shop's OWN store_settings (never hardcoded). These tests lock the
flattening: address assembly, absolute logo URL, and graceful None.
"""
from types import SimpleNamespace

import pytest

from src.db.models.supplier_model import SupplierModel
from src.routes.pos_router import _postcard_store_footer, _supplier_is_maker


def _store(**over):
    base = dict(
        store_name="Artemis Roma - Headshop",
        opening_hours="Mon–Sat 11–19",
        phone="+39 06 4890 1234",
        address_line1="Via del Corso 12",
        address_line2=None,
        city="Roma",
        postal_code="00186",
        receipt_logo_url="/static/artemis-logo.png",
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_none_store_gives_none_footer():
    assert _postcard_store_footer(None, "https://x") is None


def test_full_store_flattens_with_assembled_address_and_absolute_logo():
    f = _postcard_store_footer(_store(), "https://banco.example")
    assert f["name"] == "Artemis Roma - Headshop"
    assert f["hours"] == "Mon–Sat 11–19"
    assert f["phone"] == "+39 06 4890 1234"
    assert f["address"] == "Via del Corso 12, 00186 Roma"
    # relative logo path is made absolute for the shared/OG preview
    assert f["logo"] == "https://banco.example/static/artemis-logo.png"


def test_absolute_logo_is_left_untouched():
    f = _postcard_store_footer(_store(receipt_logo_url="https://cdn.x/logo.png"), "https://banco.example")
    assert f["logo"] == "https://cdn.x/logo.png"


def test_address_line2_is_folded_in():
    f = _postcard_store_footer(_store(address_line2="2nd floor"), "https://x")
    assert f["address"] == "Via del Corso 12, 2nd floor, 00186 Roma"


def test_missing_optional_fields_degrade_gracefully():
    f = _postcard_store_footer(
        _store(opening_hours=None, phone=None, receipt_logo_url=None,
               address_line1=None, address_line2=None, city=None, postal_code=None),
        "https://x")
    assert f["name"] == "Artemis Roma - Headshop"
    assert f["hours"] is None
    assert f["phone"] is None
    assert f["logo"] is None
    assert f["address"] is None


# ---- maker gate: "Handmade / made with love" only for real makers, not distributors ----

async def _seed_supplier(db, name, prefix, adapter_type):
    db.add(SupplierModel(code=prefix, name=name, prefix=prefix,
                         adapter_type=adapter_type, supplier_role="wholesale"))
    await db.commit()


@pytest.mark.asyncio
async def test_manual_and_incms_suppliers_are_makers(db_session):
    await _seed_supplier(db_session, "Ecolution GmbH — Sylvie Thiel", "ECO", "manual")
    await _seed_supplier(db_session, "Mama Cynthia", "MC", "incms")
    assert await _supplier_is_maker(db_session, "Ecolution GmbH — Sylvie Thiel") is True
    assert await _supplier_is_maker(db_session, "Mama Cynthia") is True


@pytest.mark.asyncio
async def test_distributors_are_not_makers(db_session):
    await _seed_supplier(db_session, "FourTwenty", "FTW", "magento")
    await _seed_supplier(db_session, "Tamar Trade GmbH", "TAM", "tamar")
    await _seed_supplier(db_session, "Edelweiss AG", "EDW", None)   # bare wholesale row
    assert await _supplier_is_maker(db_session, "FourTwenty") is False
    assert await _supplier_is_maker(db_session, "Tamar Trade GmbH") is False
    assert await _supplier_is_maker(db_session, "Edelweiss AG") is False


@pytest.mark.asyncio
async def test_missing_or_unknown_supplier_is_not_a_maker(db_session):
    assert await _supplier_is_maker(db_session, None) is False
    assert await _supplier_is_maker(db_session, "") is False
    assert await _supplier_is_maker(db_session, "Nobody Ltd") is False
