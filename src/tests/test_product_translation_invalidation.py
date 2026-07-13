"""Stale-translation fix — editing a product's base text must invalidate its cached
per-language skins so the postcard / multilingual views regenerate from the NEW wording.

The bug (found onboarding Ecolution, 2026-07-13): a manager tightened a long imported
description to a short one, but the postcard kept serving the old long text in every
language. Root cause: ``ensure_description`` returns the first stored translation row
forever and ``update_product`` never cleared them. These tests lock the contract at the
service layer — fast, deterministic, no LLM call (they exercise only the source-language
path, which reads the base directly).
"""
import uuid

import pytest

from src.db.models.product_model import ProductModel, ProductTranslationModel
from src.services.product_translations import ensure_description, invalidate_translations


async def _make_product(db, *, description: str, source_lang: str = "en") -> ProductModel:
    p = ProductModel(
        sku=f"ECO-{uuid.uuid4().hex[:8]}",
        name="Deluxe Wool Glasses Case",
        price=34.59,
        description=description,
        source_lang=source_lang,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


def _add_translation(db, product, lang, description, provenance="machine"):
    db.add(ProductTranslationModel(
        product_id=product.id, lang=lang, name=None, description=description,
        provenance=provenance, needs_review=provenance == "machine",
    ))


@pytest.mark.asyncio
async def test_invalidate_clears_only_that_products_rows(db_session):
    """invalidate_translations drops every cached skin for the product and returns the
    count — and never touches a different product's rows."""
    keep = await _make_product(db_session, description="Keep me")
    target = await _make_product(db_session, description="Old long text")
    _add_translation(db_session, keep, "de", "Behalte mich")
    _add_translation(db_session, target, "de", "Alter langer Text")
    _add_translation(db_session, target, "fr", "Ancien texte long")
    _add_translation(db_session, target, "en", "Old long text", provenance="source")
    await db_session.commit()

    cleared = await invalidate_translations(db_session, target.id)
    assert cleared == 3

    from sqlalchemy import select
    rows = (await db_session.execute(
        select(ProductTranslationModel).where(
            ProductTranslationModel.product_id == target.id))).scalars().all()
    assert rows == []
    # The other product's skin survives.
    kept = (await db_session.execute(
        select(ProductTranslationModel).where(
            ProductTranslationModel.product_id == keep.id))).scalars().all()
    assert len(kept) == 1


@pytest.mark.asyncio
async def test_invalidate_on_empty_is_noop(db_session):
    """No cached rows → returns 0, no error (the common 'price-only edit' path)."""
    p = await _make_product(db_session, description="anything")
    assert await invalidate_translations(db_session, p.id) == 0


@pytest.mark.asyncio
async def test_stale_hit_is_served_until_invalidated_then_regenerates(db_session):
    """The bug and the fix in one test. A stale source-language row is served verbatim
    (that's the bug); after invalidation, ensure_description regenerates from the current
    base description (that's the fix). Source-language path — no LLM."""
    p = await _make_product(db_session, description="SHORT new text", source_lang="en")
    # Simulate the stale cache: an EN row still holding the OLD long text.
    _add_translation(db_session, p, "en", "OLD long wall of text", provenance="source")
    await db_session.commit()

    # Before the fix's effect: ensure_description hands back the stale hit.
    before = await ensure_description(db_session, p, "en")
    assert before["description"] == "OLD long wall of text"

    # Apply the fix: invalidate, then re-read.
    await invalidate_translations(db_session, p.id)
    after = await ensure_description(db_session, p, "en")
    assert after["description"] == "SHORT new text"
    assert after["provenance"] == "source"

    # And the regenerated row is now persisted (next view is a stored hit again).
    from sqlalchemy import select
    rows = (await db_session.execute(
        select(ProductTranslationModel).where(
            ProductTranslationModel.product_id == p.id))).scalars().all()
    assert len(rows) == 1
    assert rows[0].description == "SHORT new text"
