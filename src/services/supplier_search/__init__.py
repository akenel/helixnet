"""Live supplier-site search — SUPPLIER-LIST-DRIVEN registry + orchestrator.

The supplier list IS the registry (Angel's model): every supplier row carries a website
(`source_url`) and a platform (`adapter_type`). Live search iterates the shop's active
suppliers that have a website, dispatches each to the PLATFORM adapter for its type
(Magento / Tamar / Shopware …) pointed at that supplier's URL, and runs them concurrently.

Adding a supplier's live search = set its website + platform, done. If the platform isn't
set (or isn't a web platform, e.g. a `csv` importer), we SNIFF the homepage to detect it —
so "just point at the website" works even without a hand-set type. A brand-new platform =
write that one adapter once, and every supplier on it is covered forever.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from .base import BaseAdapter, SupplierResult, make_client
from .magento import MagentoAdapter
from .query_i18n import query_variants
from .shopware import ShopwareAdapter
from .tamar import TamarAdapter

log = logging.getLogger("supplier_search")

# platform key (SupplierModel.adapter_type or a sniffed value) -> platform adapter class.
PLATFORM_ADAPTERS: dict[str, type[BaseAdapter]] = {
    "magento": MagentoAdapter,
    "tamar": TamarAdapter,
    "shopware": ShopwareAdapter,
}


def detect_platform(homepage_html: str | None) -> str | None:
    """Sniff a shop's platform from its homepage HTML (for suppliers whose adapter_type isn't
    a web platform). Cheap, marker-based; returns None if unrecognised (no live search)."""
    h = homepage_html or ""
    low = h.lower()
    if "ssearch" in low or "shopware" in low:
        return "shopware"
    if "/api/shop/products" in h or 'id="productsapiurl"' in low or "instantsearchtext" in low:
        return "tamar"
    if "catalogsearch" in low or "amasty" in low or "/static/version" in low or "mage/" in low or "magento" in low:
        return "magento"
    return None


async def _adapters_for_suppliers(db, client, suppliers: list[str] | None) -> list[BaseAdapter]:
    """Build the platform adapters for the shop's active suppliers that have a website.
    ``suppliers`` optionally restricts by supplier code/prefix/name (case-insensitive)."""
    from src.db.models.supplier_model import SupplierModel

    rows = (await db.execute(
        select(SupplierModel).where(SupplierModel.is_active.is_(True))
    )).scalars().all()

    want = {s.strip().lower() for s in (suppliers or []) if s.strip()}
    adapters: list[BaseAdapter] = []
    for s in rows:
        url = (s.source_url or "").strip()
        if not url:
            continue
        if want and not ({(s.code or "").lower(), (s.prefix or "").lower(), (s.name or "").lower()} & want):
            continue
        platform = (s.adapter_type or "").strip().lower()
        if platform not in PLATFORM_ADAPTERS:
            # Not a web platform (e.g. 'csv'/'manual'/unset) — sniff the homepage.
            try:
                hp = await client.get(url)
                platform = detect_platform(hp.text) or ""
            except Exception as e:
                log.warning("platform sniff failed for %s (%s): %s", s.name, url, e)
                platform = ""
        cls = PLATFORM_ADAPTERS.get(platform)
        if cls:
            adapters.append(cls(url, s.name, getattr(s, "supplier_role", None) or "wholesale"))
        else:
            log.info("supplier %s has a website but no supported platform — skipped", s.name)
    return adapters


async def search_suppliers(q: str, db, suppliers: list[str] | None = None,
                           limit: int = 4, timeout: float = 15.0) -> dict:
    """Search the shop's supplier websites live. Returns
    ``{"query", "results": [dict...], "errors": {supplier: msg}, "suppliers": [name...]}``."""
    q = (q or "").strip()
    if not q or db is None:
        return {"query": q, "results": [], "errors": {}, "suppliers": []}

    async with make_client(timeout) as client:
        adapters = await _adapters_for_suppliers(db, client, suppliers)
        if not adapters:
            return {"query": q, "results": [], "errors": {}, "suppliers": []}

        # BL-38: also search a German variant so an English/French term hits the German sites.
        variants = await query_variants(client, q, langs=("de",))

        async def _run(adapter, qv):
            return await asyncio.wait_for(adapter.search(client, qv, limit), timeout=timeout)

        jobs = [(a, qv) for a in adapters for qv in variants]
        settled = await asyncio.gather(*[_run(a, qv) for (a, qv) in jobs], return_exceptions=True)

    # Merge across (adapter × variant); dedupe the same product, keep its best score.
    by_key: dict[tuple, SupplierResult] = {}
    errors: dict[str, str] = {}
    for (adapter, qv), res in zip(jobs, settled):
        if isinstance(res, Exception):
            log.warning("supplier-search %s failed for %r: %s", adapter.supplier, qv, res)
            errors.setdefault(adapter.supplier, str(res) or res.__class__.__name__)
            continue
        for r in res:
            r.role = adapter.role       # stamp what this site's price means (cost vs market)
            key = (r.supplier, r.product_url)
            if key not in by_key or r.score > by_key[key].score:
                by_key[key] = r

    results = sorted(by_key.values(), key=lambda r: r.score, reverse=True)
    return {
        "query": q,
        "variants": variants,
        "results": [r.to_dict() for r in results],
        "errors": errors,
        "suppliers": [a.supplier for a in adapters],
    }
