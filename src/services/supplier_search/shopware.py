"""Shopware 5 live-search adapter (Near Dark and any other Shopware 5 shop).

Shopware 5 exposes a plain search (``/search?sSearch=``) whose grid links to product pages,
and those pages carry a real EAN, a ``product:price`` meta (currency carried so a EUR shop is
never mixed into a CHF till), an og image and a description. Bound to a supplier's ``base_url``.
"""
from __future__ import annotations

import asyncio
import re

import httpx

from .base import BaseAdapter, SupplierResult, clean_text, parse_chf, score_title

_RE_H1 = re.compile(r'<h1[^>]*class="[^"]*product--title[^"]*"[^>]*>(.*?)</h1>', re.S)
_RE_OG_TITLE = re.compile(r'<meta property="og:title" content="([^"]+)"')
_RE_PRICE = re.compile(r'<meta property="product:price" content="([0-9.,]+)"')
_RE_CURRENCY = re.compile(r'<meta property="product:price:currency" content="([A-Z]{3})"'
                          r'|itemprop="priceCurrency" content="([A-Z]{3})"')
_RE_EAN = re.compile(r'class="[^"]*ean[^"]*">\s*<span>EAN:</span>\s*([0-9]{8,14})')
_RE_OG_IMG = re.compile(r'<meta property="og:image" content="([^"]+)"')
_RE_DESC = re.compile(r'itemprop="description"[^>]*>(.*?)</div>', re.S)


class ShopwareAdapter(BaseAdapter):
    platform = "shopware"

    def __init__(self, base_url: str, supplier_name: str, role: str = "wholesale"):
        super().__init__(base_url, supplier_name, role)
        h = re.escape(self.host)
        # Product URLs: /<cat>/<sub>/<id>/<slug> — the numeric id before the slug is the tell.
        self._re_product_url = re.compile(
            r'href="(https?://' + h + r'/[a-z0-9/\-]+/\d+/[a-z0-9][a-z0-9.\-]*)"')
        self._re_url_cat = re.compile(
            r'https?://' + h + r'/(?:[a-z0-9\-]+/)*([a-z0-9\-]+)/\d+/')

    async def search(self, client: httpx.AsyncClient, q: str, limit: int = 5) -> list[SupplierResult]:
        r = await client.get(f"{self.base_url}/search", params={"sSearch": q})
        urls, seen = [], set()
        for m in self._re_product_url.finditer(r.text):
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
            res = self._parse(pr.text, str(pr.url), q)
            if res:
                out.append(res)
        return out

    def _parse(self, html: str, url: str, q: str) -> SupplierResult | None:
        tm = _RE_H1.search(html) or _RE_OG_TITLE.search(html)
        title = clean_text(tm.group(1)) if tm else ""
        if not title:
            return None

        pm = _RE_PRICE.search(html)
        price = parse_chf(pm.group(1)) if pm else None
        cm = _RE_CURRENCY.search(html)
        currency = (cm.group(1) or cm.group(2)) if cm else "EUR"

        em = _RE_EAN.search(html)
        barcode = em.group(1) if em else None

        im = _RE_OG_IMG.search(html)
        image = im.group(1) if im else None

        dm = _RE_DESC.search(html)
        description = clean_text(dm.group(1), 600) if dm else None

        catm = self._re_url_cat.search(url)
        category = catm.group(1).replace("-", " ").title() if catm else None

        return SupplierResult(
            supplier=self.supplier, title=title, product_url=url,
            price=price, currency=currency, image_url=image, barcode=barcode,
            description=description, category=category,
            price_tiers=[], tier_mode="per_unit",
            score=score_title(q, title),
        )
