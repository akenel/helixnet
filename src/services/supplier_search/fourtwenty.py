"""FourTwenty (fourtwenty.ch) live-search adapter — Magento 2 + Amasty search.

Felix buys ~90% from FourTwenty / Tamar. FourTwenty's Amasty AJAX autocomplete WAF-blocks
direct hits (403), but its plain search page works and is friendlier: for an unambiguous
query ``catalogsearch/result/?q=`` 302-redirects straight to the product page; for several
hits it lands on ``/search/<q>`` with a ``product-item-link`` grid. Product pages are stable
server-rendered HTML carrying title, final price, EAN, gallery image, description AND the
Magento tier-price ladder (``priceConfig.tierPrices``) — so we suck the quantity breaks in too.
"""
from __future__ import annotations

import asyncio
import json
import re

import httpx

from .base import BaseAdapter, SupplierResult, clean_text, money2, score_title

BASE = "https://fourtwenty.ch"

_RE_TITLE = re.compile(r'data-ui-id="page-title-wrapper"[^>]*>([^<]+)')
_RE_PRICE_META = re.compile(r'itemprop="price"\s+content="([0-9.]+)"')
_RE_PRICE_FINAL = re.compile(
    r'data-price-type="finalPrice"[^>]*data-price-amount="([0-9.]+)"'
    r'|data-price-amount="([0-9.]+)"[^>]*data-price-type="finalPrice"'
)
_RE_CURRENCY = re.compile(r'itemprop="priceCurrency"\s+content="([A-Z]{3})"')
_RE_TIERS = re.compile(r'"tierPrices":(\[.*?\])')
_RE_IMG = re.compile(
    r'"img":"(https:\\?/\\?/fourtwenty\.ch\\?/media\\?/catalog\\?/product[^"]+?\.(?:jpe?g|png|webp))"'
)
_RE_OG_IMG = re.compile(r'<meta property="og:image" content="([^"]+)"')
_RE_EAN = re.compile(r'(?:EAN|GTIN|Barcode)\D{0,40}?([0-9]{12,14})', re.I)
_RE_DESC = re.compile(
    r'class="product attribute description".*?<div class="value"[^>]*>(.*?)</div>', re.S
)
_RE_GRID = re.compile(
    r'class="product-item-link"[^>]*href="(https://fourtwenty\.ch/[a-z0-9][a-z0-9\-]*\.html)"'
)
_RE_BREADCRUMB = re.compile(r'"@type":\s*"ListItem",\s*"position":\s*\d+,\s*"name":\s*"([^"]+)"')


class FourTwentyAdapter(BaseAdapter):
    supplier = "FourTwenty"
    supplier_key = "fourtwenty"

    async def search(self, client: httpx.AsyncClient, q: str, limit: int = 5) -> list[SupplierResult]:
        r = await client.get(f"{BASE}/catalogsearch/result/", params={"q": q})
        final_url, html = str(r.url), r.text

        if self._is_product_page(final_url, html):
            res = self._parse_product(html, final_url, q)
            return [res] if res else []

        # results grid -> take the first `limit` distinct product pages, fetch concurrently
        urls, seen = [], set()
        for m in _RE_GRID.finditer(html):
            u = m.group(1)
            if u not in seen:
                seen.add(u)
                urls.append(u)
            if len(urls) >= limit:
                break
        if not urls:
            return []
        pages = await asyncio.gather(*[client.get(u) for u in urls], return_exceptions=True)
        out = []
        for pr in pages:
            if isinstance(pr, Exception):
                continue
            res = self._parse_product(pr.text, str(pr.url), q)
            if res:
                out.append(res)
        return out

    @staticmethod
    def _is_product_page(url: str, html: str) -> bool:
        return (url.endswith(".html") and "/search/" not in url
                and 'data-ui-id="page-title-wrapper"' in html and 'data-role="priceBox"' in html)

    @classmethod
    def _parse_product(cls, html: str, url: str, q: str) -> SupplierResult | None:
        tm = _RE_TITLE.search(html)
        title = clean_text(tm.group(1)) if tm else ""
        if not title:
            return None

        pm = _RE_PRICE_META.search(html) or _RE_PRICE_FINAL.search(html)
        price = None
        if pm:
            price = float(next(g for g in pm.groups() if g))
        cur = _RE_CURRENCY.search(html)
        currency = cur.group(1) if cur else "CHF"

        img = None
        im = _RE_IMG.search(html) or _RE_OG_IMG.search(html)
        if im:
            img = im.group(1).replace("\\/", "/")

        em = _RE_EAN.search(html)
        barcode = em.group(1) if em else None

        dm = _RE_DESC.search(html)
        description = clean_text(dm.group(1), 600) if dm else None

        crumbs = _RE_BREADCRUMB.findall(html)
        # last crumb is the product itself; the one before it is the leaf category
        category = crumbs[-2] if len(crumbs) >= 2 else (crumbs[-1] if crumbs else None)

        return SupplierResult(
            supplier=cls.supplier, title=title, product_url=url,
            price=price, currency=currency, image_url=img, barcode=barcode,
            description=description, category=category,
            price_tiers=cls._tiers(html, price), tier_mode="per_unit",
            score=score_title(q, title),
        )

    @staticmethod
    def _tiers(html: str, base_price) -> list:
        """Magento tierPrices are per-unit ('12 für jeweils 4.00'). Build a per_unit ladder
        with the base as the min_qty=1 rung. Return [] unless there's a real break."""
        if base_price is None:
            return []
        tiers = [{"min_qty": 1, "unit_price": money2(base_price)}]
        m = _RE_TIERS.search(html)
        if m:
            try:
                for t in json.loads(m.group(1)):
                    qty, pr = int(t.get("qty")), t.get("price")
                    if qty >= 2 and pr is not None:
                        tiers.append({"min_qty": qty, "unit_price": money2(pr)})
            except (ValueError, TypeError):
                pass
        tiers.sort(key=lambda r: r["min_qty"])
        return tiers if len(tiers) > 1 else []
