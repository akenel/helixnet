"""BL-CAT — ensure_description source_lang honesty.

The disease: `source_lang` lies 'en' all over the catalogue, so a GERMAN base description was served
to an ENGLISH user stamped as authoritative 'source' English ("the English is still German"). The fix:
detect German confidently, let it override the lie, translate for other languages, and never mint an
authoritative skin from an unverified source.
"""
import uuid

import pytest

from src.db.models.product_model import ProductModel, ProductTranslationModel
from src.services import product_translations as pt
from src.services.product_translations import ensure_description, _guess_base_lang


async def _mk(db, *, description, source_lang="en", source_url=""):
    p = ProductModel(sku=f"SLH-{uuid.uuid4().hex[:8]}", name="Test", price=1.0,
                     description=description, source_lang=source_lang, source_url=source_url)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


def test_guess_base_lang():
    assert _guess_base_lang("Feuerzeug mit Sturmflamme und robustem Gehäuse") == "de"
    assert _guess_base_lang("Hochwertige Drehpapier Blättchen, ohne Chlor") == "de"
    assert _guess_base_lang("A sturdy metal lighter with a windproof flame") is None
    assert _guess_base_lang("Briquet tempête en métal robuste") is None
    assert _guess_base_lang("") is None
    # a lone umlaut brand in short English text must NOT trip 'de'
    assert _guess_base_lang("Motörhead sticker") is None


@pytest.mark.asyncio
async def test_german_base_served_native_for_de_and_source_healed(db_session):
    """German base + lying source_lang='en'. A German viewer gets the base as authoritative 'source',
    and the lie is healed to 'de' for next time."""
    p = await _mk(db_session, description="Feuerzeug mit Sturmflamme, hochwertig und ohne Gas.",
                  source_lang="en")
    out = await ensure_description(db_session, p, "de")
    assert out["provenance"] == "source"
    assert out["description"].startswith("Feuerzeug")
    await db_session.refresh(p)
    assert p.source_lang == "de"    # self-healed the 'en' lie


@pytest.mark.asyncio
async def test_german_base_is_TRANSLATED_for_english_not_served_raw(db_session, monkeypatch):
    """The exact bug: an English viewer must NOT get the raw German stamped as authoritative 'source'
    — it gets a machine translation flagged needs_review."""
    async def _fake_translate(text, tgt, src="en"):
        return f"[EN of {src}] a windproof lighter"
    monkeypatch.setattr(pt, "_translate", _fake_translate)

    p = await _mk(db_session, description="Feuerzeug mit Sturmflamme und robustem Gehäuse.",
                  source_lang="en")
    out = await ensure_description(db_session, p, "en")
    assert out["provenance"] == "machine"          # translated, NOT authoritative German-as-English
    assert "windproof" in out["description"]
    assert "Feuerzeug" not in out["description"]
    # the stored skin is flagged for review
    row = (await db_session.execute(
        ProductTranslationModel.__table__.select().where(
            ProductTranslationModel.product_id == p.id))).mappings().first()
    assert row["needs_review"] is True


@pytest.mark.asyncio
async def test_real_english_base_stays_authoritative(db_session):
    """A genuine English base with source_lang='en' still serves as authoritative 'source' (verified)."""
    p = await _mk(db_session, description="A sturdy windproof metal lighter with a refillable tank.",
                  source_lang="en")
    out = await ensure_description(db_session, p, "en")
    assert out["provenance"] == "source"
    row = (await db_session.execute(
        ProductTranslationModel.__table__.select().where(
            ProductTranslationModel.product_id == p.id))).mappings().first()
    assert row["needs_review"] is False


@pytest.mark.asyncio
async def test_unverified_source_is_flagged_not_authoritative(db_session):
    """No source_lang at all + no German smell → served as base but flagged needs_review (we're
    guessing 'en', not certain)."""
    p = await _mk(db_session, description="Windproof lighter refillable metal.", source_lang=None)
    out = await ensure_description(db_session, p, "en")
    assert out["provenance"] == "source"
    row = (await db_session.execute(
        ProductTranslationModel.__table__.select().where(
            ProductTranslationModel.product_id == p.id))).mappings().first()
    assert row["needs_review"] is True   # unverified — don't claim authority
