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


# German function words that do NOT appear in EN/FR/IT retail copy — an unambiguous German signal.
_DE_WORDS = re.compile(
    r"\b(und|oder|mit|für|ohne|nicht|auch|sowie|inkl|beim|zum|zur|Grösse|Größe|Stück|Zubehör|"
    r"Farbe|geeignet|hochwertig|Packung|Beutel|Schachtel|Drehpapier|Feuerzeug|Blättchen)\b", re.I)
_UMLAUT = re.compile(r"[äöüÄÖÜß]")


def _guess_base_lang(text: str | None) -> str | None:
    """Best-effort, CONSERVATIVE source-language guess for a product's base description.

    Returns 'de' only when we're confident (a German function word, or umlauts in enough text) —
    else None ("unknown, don't override"). Deliberately one-sided: the disease is German base text
    stored with a lying source_lang='en' (see banco-category-language-mess), which makes English
    users read German stamped as authoritative English. A false 'de' would wrongly translate real
    English, so we only claim German on strong evidence; EN/FR/IT fall through to the stored source.
    """
    t = text or ""
    if _DE_WORDS.search(t):
        return "de"
    if _UMLAUT.search(t) and len(t) > 40:   # umlauts + real length, not a lone brand like Motörhead
        return "de"
    return None


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

    base = (product.description or "").strip()
    # HONEST source language (BL-CAT): source_lang lies 'en' all over the catalogue. A confident
    # German smell overrides that lie; a stored value is used only if we have no counter-signal;
    # else we assume 'en' but treat it as UNVERIFIED (never mint an authoritative skin from it).
    stored_src = _norm(product.source_lang) if (product.source_lang or "").strip() else None
    guessed = _guess_base_lang(base)
    true_src = guessed or stored_src or "en"
    source_verified = bool(guessed) or (stored_src is not None)
    # Self-heal the lie: base is clearly German but stored en/null → correct source_lang for next time.
    if guessed == "de" and stored_src != "de":
        product.source_lang = "de"

    name = desc = None
    provenance = "machine"
    needs_review = True

    if is_tamar_product(product):
        async with httpx.AsyncClient() as client:
            name, desc = await _fetch_tamar(client, product.source_url, lang)
        if desc:
            provenance, needs_review = "source", False   # native per-language fetch is authoritative

    if not desc and base:
        if lang == true_src:
            # base IS in this language. Authoritative only if the source was verified; an assumed
            # 'en' with no signal is served but flagged for review (don't claim authority on a guess).
            desc, provenance = base, "source"
            needs_review = not source_verified
        else:
            desc = await _translate(base, lang, true_src)
            provenance, needs_review = "machine", True

    if desc:
        if hit:
            hit.description = desc
            hit.name = name or hit.name
            hit.provenance = provenance
            hit.needs_review = needs_review
        else:
            db.add(ProductTranslationModel(
                product_id=product.id, lang=lang, name=name, description=desc,
                provenance=provenance, needs_review=needs_review))
        await db.commit()
        return {"lang": lang, "description": desc, "name": name, "provenance": provenance}

    # Nothing to fill from — hand back the raw base so the UI still shows *something*.
    return {"lang": lang, "description": product.description, "name": product.name,
            "provenance": "base", "fallback": True}
