"""BL-CAT anti-regrowth funnel — every new product's category is canonicalized on create.

After the 61-German-slug catalogue was migrated to one clean 2-level tree, the durable fix is a
chokepoint: no create path may write a fresh free-text category again. These lock the canonicalizer
and prove the create/quick-add paths funnel through it (unknown/blank -> Unsorted, tree never regrows).
"""
import uuid

import pytest

from src.services.catalog_taxonomy import canonicalize_category, CANONICAL_CATEGORIES
from src.schemas.pos_schema import ProductCreate
from src.routes import pos_router


def _sku():
    return "FNL-" + uuid.uuid4().hex[:8]


_USER = {"username": "pam", "roles": ["pos-cashier"]}


def test_canonicalize_known_slugs():
    assert canonicalize_category("Feuerzeuge") == ("Lighters", "Smoking Gear")
    assert canonicalize_category("Oel Dabbing") == ("Dab & Concentrate Gear", "Smoking Gear")
    assert canonicalize_category("Marijuana") == ("CBD Flower", "CBD & Hemp")
    assert canonicalize_category("Zubehoer") == ("Accessories (general)", "Unsorted / System")


def test_canonicalize_unknown_and_blank_go_unsorted():
    for bad in ("Flower", "Drinks", "Totally Made Up", "", None, "   "):
        assert canonicalize_category(bad) == ("Unsorted", "Unsorted / System")


def test_canonicalize_is_case_insensitive_and_idempotent():
    assert canonicalize_category("feuerzeuge") == ("Lighters", "Smoking Gear")
    # already-canonical stays put (idempotent — safe to run twice)
    assert canonicalize_category("Lighters") == ("Lighters", "Smoking Gear")
    assert canonicalize_category("Dab & Concentrate Gear")[0] == "Dab & Concentrate Gear"


def test_every_canonical_category_maps_to_a_group():
    for c in CANONICAL_CATEGORIES:
        cat, grp = canonicalize_category(c)
        assert cat == c and grp, f"{c} did not resolve to a group"


@pytest.mark.asyncio
async def test_create_product_funnels_german_slug(db_session):
    p = ProductCreate(name="BIC mini", price=1.50, category="Feuerzeuge", sku=_sku())
    out = await pos_router.create_product(p, db=db_session, current_user=_USER)
    assert out.category == "Lighters"
    assert out.product_group == "Smoking Gear"


@pytest.mark.asyncio
async def test_create_product_unknown_lands_unsorted(db_session):
    p = ProductCreate(name="Mystery Item", price=2.00, category="Some New Bucket", sku=_sku())
    out = await pos_router.create_product(p, db=db_session, current_user=_USER)
    assert out.category == "Unsorted"
    assert out.product_group == "Unsorted / System"


@pytest.mark.asyncio
async def test_quick_create_blank_category_lands_unsorted(db_session):
    p = ProductCreate(name="On-the-fly cup", price=3.00, sku=_sku())
    out = await pos_router.quick_create_product(p, db=db_session, current_user=_USER)
    assert out.category == "Unsorted"
    assert out.product_group == "Unsorted / System"
