"""BL-36 — per-language product descriptions (the `product_translations` table).

A product = one language-independent CORE + N text skins. We fill the skins from the richest
source: a Tamar/Artemis product publishes DE/EN/FR/IT NATIVELY (free fetch → provenance
'source'); everything else is machine-translated from the base description (Ollama →
provenance 'machine', needs_review). Display picks the operator's language, falls back to
English, then the raw base description. Filled ON DEMAND (first view in a language fills it,
then it's a stored hit forever) so there is no giant up-front backfill.
"""
from __future__ import annotations

import html as _html
import logging
import os
import re
from urllib.parse import urlparse

import httpx
from sqlalchemy import delete, select

from src.db.models.product_model import ProductTranslationModel

log = logging.getLogger("product_translations")

# The shop's languages. Artemis serves the first four natively; extend (nl/es/…) any time —
# extra languages just machine-translate from the base. Kept as an env override for flexibility.
TARGET_LANGS = tuple((os.getenv("BANCO_CATALOG_LANGS") or "en,de,fr,it").split(","))
LANG_NAMES = {"en": "English", "de": "German", "fr": "French", "it": "Italian",
              "nl": "Dutch", "es": "Spanish", "pl": "Polish"}

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Tamar (artemisluzern.ch) publishes every language at the same slug under a per-lang path.
_TAMAR_PATHS = {"de": "/de/produkt/", "en": "/en/product/", "fr": "/fr/produit/", "it": "/it/prodotto/"}
_TAMAR_TAIL = re.compile(r"/(?:de|en|fr|it)/(?:produkt|product|produit|prodotto)/(.+)$", re.I)
_RE_DESC = re.compile(r'id="Description"[^>]*>(.*?)</div>', re.S)
_RE_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)


def _clean(s: str | None, limit: int = 2000) -> str | None:
    if not s:
        return None
    s = _html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] or None


def _norm(lang: str | None) -> str:
    return (lang or "en").strip().lower()[:2]


def is_tamar_product(product) -> bool:
    """A product we can fetch native per-language text for (Tamar /xx/prod…/slug URL)."""
    return bool(_TAMAR_TAIL.search(product.source_url or ""))


def _tamar_url(source_url: str, lang: str) -> str | None:
    m = _TAMAR_TAIL.search(source_url or "")
    if not m or lang not in _TAMAR_PATHS:
        return None
    p = urlparse(source_url)
    return f"{p.scheme}://{p.netloc}{_TAMAR_PATHS[lang]}{m.group(1)}"


async def _fetch_tamar(client: httpx.AsyncClient, source_url: str, lang: str):
    """Native (name, description) for `lang` off the Tamar detail page, or (None, None)."""
    url = _tamar_url(source_url, lang)
    if not url:
        return None, None
    try:
        r = await client.get(url, headers={"User-Agent": _UA}, follow_redirects=True, timeout=20)
        html = r.text
    except Exception as e:  # noqa: BLE001
        log.warning("tamar fetch %s %s failed: %s", lang, url, e)
        return None, None
    hm, dm = _RE_H1.search(html), _RE_DESC.search(html)
    return (_clean(hm.group(1), 255) if hm else None), (_clean(dm.group(1), 2000) if dm else None)


async def _translate(text: str, tgt_lang: str, src_lang: str = "en") -> str | None:
    """Machine-translate a product description (Ollama Turbo/local). Names left to the model's
    judgement via the system prompt (brands stay). Returns None on any failure (caller falls back)."""
    from src.llm import run_llm, turbo_or_local
    system = (
        f"You translate retail product descriptions from {LANG_NAMES.get(src_lang, src_lang)} "
        f"to {LANG_NAMES.get(tgt_lang, tgt_lang)}. Translate faithfully and concisely. Keep brand "
        f"and product names, units, and numbers unchanged. Output ONLY the translated description "
        f"— no preamble, no quotes, no notes."
    )
    try:
        res = await run_llm(text, target=turbo_or_local("gpt-oss:120b"), system=system)
        return (res.text or "").strip() or None
    except Exception as e:  # noqa: BLE001
        log.warning("translate ->%s failed: %s", tgt_lang, e)
        return None


async def invalidate_translations(db, product_id) -> int:
    """Drop the cached per-language skins for a product so ``ensure_description`` refills
    them from the CURRENT base text on the next view.

    Call this whenever the base name/description changes. The stored translations are
    DERIVED text — machine-translated (or fetched) from the base at first view — and go
    stale silently otherwise: a manager rewrites a description, but the postcard keeps
    serving the old wording because ``ensure_description`` returns the first stored hit
    forever. Clearing the rows is cheap (they refill on demand, only for the languages
    actually viewed) and needs no schema change. Returns the number of rows cleared."""
    res = await db.execute(
        delete(ProductTranslationModel).where(ProductTranslationModel.product_id == product_id)
    )
    await db.commit()
    return res.rowcount or 0


async def ensure_description(db, product, lang: str) -> dict:
    """Best description for `lang`, filling `product_translations` on demand.

    Order: stored row → Tamar native fetch → machine-translate the base → raw base/EN fallback.
    Returns ``{lang, description, name, provenance, fallback?}``."""
    lang = _norm(lang)
    rows = (await db.execute(
        select(ProductTranslationModel).where(ProductTranslationModel.product_id == product.id)
    )).scalars().all()
    existing = {t.lang: t for t in rows}

    hit = existing.get(lang)
    if hit and (hit.description or "").strip():
        return {"lang": lang, "description": hit.description, "name": hit.name,
                "provenance": hit.provenance}

    src_lang = _norm(product.source_lang or "en")
    base = (product.description or "").strip()
    name = desc = None
    provenance = "machine"

    if is_tamar_product(product):
        async with httpx.AsyncClient() as client:
            name, desc = await _fetch_tamar(client, product.source_url, lang)
        if desc:
            provenance = "source"

    if not desc and base:
        if lang == src_lang:
            desc, provenance = base, "source"
        else:
            desc = await _translate(base, lang, src_lang)
            provenance = "machine"

    if desc:
        if hit:
            hit.description = desc
            hit.name = name or hit.name
            hit.provenance = provenance
            hit.needs_review = provenance == "machine"
        else:
            db.add(ProductTranslationModel(
                product_id=product.id, lang=lang, name=name, description=desc,
                provenance=provenance, needs_review=provenance == "machine"))
        await db.commit()
        return {"lang": lang, "description": desc, "name": name, "provenance": provenance}

    # Nothing to fill from — hand back the raw base so the UI still shows *something*.
    return {"lang": lang, "description": product.description, "name": product.name,
            "provenance": "base", "fallback": True}
