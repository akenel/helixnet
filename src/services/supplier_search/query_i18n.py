"""BL-38 — translate a live-search QUERY into a site's language.

The supplier sites index in their own tongue: FourTwenty and Near Dark are German, Artemis
carries all four. So an English/French-typed term ("lighter gas") misses the German shelves
("Feuerzeug Gas"). Here we translate the SEARCH TERM (terse — 1-5 words, not a sentence) so
each site is queried in a language it actually indexes. In-memory cached per (term, lang)
so a repeated search costs nothing. Login language is irrelevant — it's the query word.
"""
from __future__ import annotations

import logging

log = logging.getLogger("supplier_search.query")

_LANG_NAMES = {"de": "German", "en": "English", "fr": "French", "it": "Italian"}
_CACHE: dict[tuple[str, str], str | None] = {}   # (q_lower, target) -> translated term


async def translate_query(q: str, target: str, client=None) -> str | None:
    """A short product-search term translated into `target`. None on failure (caller falls back)."""
    q = (q or "").strip()
    if not q:
        return None
    key = (q.lower(), target)
    if key in _CACHE:
        return _CACHE[key]
    from src.llm import run_llm, turbo_or_local
    system = (
        f"You translate a short head-shop PRODUCT-SEARCH term into {_LANG_NAMES.get(target, target)} "
        "as a customer of that country would actually type it. Output ONLY the search term (1-5 words) "
        "— no sentence, no quotes, no notes. Keep brand/product names unchanged (Tycoon, Zippo, RAW, "
        "Vozol). Keep common industry loanwords that shoppers use natively (e.g. in German: Grinder, "
        "Vaporizer, Papers, Bong, Shisha stay as-is)."
    )
    out = None
    try:
        res = await run_llm(q, target=turbo_or_local("gpt-oss:120b"), system=system, client=client)
        txt = (res.text or "").strip().strip('"').splitlines()
        out = (txt[0].strip()[:80] or None) if txt else None
    except Exception as e:  # noqa: BLE001
        log.warning("query translate %r -> %s failed: %s", q, target, e)
    _CACHE[key] = out
    return out


async def query_variants(client, q: str, langs=("de",)) -> list[str]:
    """The distinct query strings to actually search: the original + a translation into each
    `lang`, deduped case-insensitively (a same-language translation collapses to one search)."""
    q = (q or "").strip()
    if not q:
        return []
    variants, seen = [q], {q.lower()}
    for lang in langs:
        t = await translate_query(q, lang, client)
        if t and t.lower() not in seen:
            variants.append(t)
            seen.add(t.lower())
    return variants
