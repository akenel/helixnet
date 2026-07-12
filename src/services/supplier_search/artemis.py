"""Artemis Lucerne (artemisluzern.ch) live-search adapter — Tamar platform, JSON API.

Artemis IS Felix's own shop, but its live site is worth searching: it has a clean JSON
search API (``/api/shop/products?...&searchTerms=``) AND — the prize — English product
DESCRIPTIONS on the /en/ detail pages plus a real quantity-break (Staffel) ladder. So this
catches brand-new Artemis items not yet imported and hands back the English text + tiers.

Two hops: (1) the search API returns name/price/image/link; (2) each /en/ detail page yields
the English description, the ``BulkPrices`` tier table, and the breadcrumb category. Artemis
does not publish an EAN on the page, so live Artemis results carry no barcode (fine — the
operator adopts by name/price/photo)."""
from __future__ import annotations

import asyncio
import json
import re

import httpx

from .base import BaseAdapter, SupplierResult, clean_text, money2, parse_chf, score_title

BASE = "https://www.artemisluzern.ch"
# languageId 3 = English; loadingType 79 = the instant-search list.
SEARCH_API = f"{BASE}/api/shop/products?loadingType=79&languageId=3&displayType=3&page=1&searchTerms="

_RE_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
_RE_SALES = re.compile(r'class="SalesPrice">\s*([^<]+?)\s*</span>')
_RE_BULK = re.compile(r'<table class="BulkPrices">(.*?)</table>', re.S)
_RE_BULK_ROW = re.compile(
    r'<td class="Currency">([^<]*)</td>\s*<td class="Price1">([^<]*)</td>\s*'
    r'<td class="Price2">([^<]*)</td>.*?<td class="Amount">([^<]*)</td>', re.S)
_RE_DESC = re.compile(r'id="Description"[^>]*>(.*?)</div>', re.S)
_RE_IMG = re.compile(r'(/ProductImage\.ashx\?[^"\'<> ]+)')
_RE_CRUMB = re.compile(r'class="Breadcrumps">(.*?)</p>', re.S)


class ArtemisAdapter(BaseAdapter):
    supplier = "Artemis"
    supplier_key = "artemis"

    async def search(self, client: httpx.AsyncClient, q: str, limit: int = 5) -> list[SupplierResult]:
        r = await client.get(SEARCH_API + q, headers={"Accept": "application/json",
                                                       "X-Requested-With": "XMLHttpRequest"})
        try:
            listing = r.json().get("products", [])
        except (json.JSONDecodeError, ValueError):
            return []
        listing = [p for p in listing if p.get("linkUrl")][:limit]
        if not listing:
            return []
        pages = await asyncio.gather(
            *[client.get(BASE + p["linkUrl"]) for p in listing], return_exceptions=True)
        out = []
        for p, pr in zip(listing, pages):
            html = "" if isinstance(pr, Exception) else pr.text
            res = self._build(p, html, q)
            if res:
                out.append(res)
        return out

    @classmethod
    def _build(cls, listed: dict, html: str, q: str) -> SupplierResult | None:
        title = clean_text(listed.get("name") or "")
        if not title and html:
            m = _RE_H1.search(html)
            title = clean_text(m.group(1)) if m else ""
        if not title:
            return None

        price = parse_chf(listed.get("salesPriceText"))
        if price is None and html:
            m = _RE_SALES.search(html)
            price = parse_chf(m.group(1)) if m else None

        img = None
        cover = listed.get("coverUrl")
        if cover:
            img = cover if cover.startswith("http") else BASE + cover
        elif html:
            m = _RE_IMG.search(html)
            if m:
                img = BASE + m.group(1).replace("&amp;", "&")

        description = category = None
        if html:
            dm = _RE_DESC.search(html)
            if dm:
                description = clean_text(dm.group(1), 600)
            cm = _RE_CRUMB.search(html)
            if cm:
                crumbs = [clean_text(x) for x in re.findall(r'>([^<]+)</a>', cm.group(1))]
                category = crumbs[-1] if crumbs else None

        return SupplierResult(
            supplier=cls.supplier, title=title, product_url=BASE + listed["linkUrl"],
            price=price, currency="CHF", image_url=img, barcode=None,
            description=description, category=category,
            price_tiers=cls._tiers(html, price), tier_mode="per_unit",
            score=score_title(q, title),
        )

    @staticmethod
    def _tiers(html: str, base_price) -> list:
        """Parse the ``BulkPrices`` Staffel table ('from N pieces' @ CHF x.yy) into a per_unit
        ladder with the base as the min_qty=1 rung. [] unless there's a real break."""
        if base_price is None or not html:
            return []
        m = _RE_BULK.search(html)
        if not m:
            return []
        tiers = [{"min_qty": 1, "unit_price": money2(base_price)}]
        for cur, p1, p2, amt in _RE_BULK_ROW.findall(m.group(1)):
            price = parse_chf(f"{p1.strip().rstrip('.')}.{p2.strip() or '0'}")
            qm = re.search(r"(\d+)", amt)
            if price is not None and qm:
                qty = int(qm.group(1))
                if qty >= 2:
                    tiers.append({"min_qty": qty, "unit_price": money2(price)})
        tiers.sort(key=lambda t: t["min_qty"])
        return tiers if len(tiers) > 1 else []
