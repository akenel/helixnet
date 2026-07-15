"""Tier-2 product identification from the WEB — free, keyless (Felix's "search the web" idea).

Resolve an unknown product by its BARCODE against free barcode databases, so the till/receiving can
auto-fill title + brand + category + description + images and the human just confirms. NEVER raises —
degrades to a manual Google link. Careful, per Angel's brief:
  • QUOTA-AWARE — UPCitemdb's free trial is ~100/day; we surface exactly how many are left so the
    operator uses them wisely, and stop hitting it at 0.
  • GRACEFUL FALLBACK — over quota / not found → Open Products Facts (unlimited) → the Google URL.
  • RICH — return ALL images (the operator may want a different one) + brand/category/description.
  • LANGUAGE-CAREFUL — web data comes in many languages (OPF gave Dutch for a BIC); we flag the
    likely language so the caller can offer a translate, never silently trust it.

Cost note: a barcode is looked up ONCE ever (learn-back → cataloged forever), so free tiers suffice.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import httpx

_UPCITEMDB_TRIAL = "https://api.upcitemdb.com/prod/trial/lookup"
_OPF = "https://world.openproductsfacts.org/api/v0/product/{}.json"
_TIMEOUT = 12


def _google_url(barcode: str, name: str) -> str | None:
    q = " ".join(x for x in (barcode, name) if x).strip()
    return "https://www.google.com/search?q=" + quote_plus(q) if q else None


async def lookup_product(barcode: str | None, name: str | None = None) -> dict:
    """Barcode (primary) → a UI-ready product dict. Keyless + free. Never raises.

    Returns: {found, source, title, brand, category, description, images[], lang_hint,
              quota:{remaining,limit,reset,source}|None, google_url, note}.
    `note`: 'no_barcode' | 'quota_exhausted' | 'not_found' | None.
    """
    barcode = (barcode or "").strip()
    name = (name or "").strip()
    out: dict = {
        "found": False, "source": None, "title": None, "brand": None, "category": None,
        "description": None, "images": [], "lang_hint": None, "quota": None,
        "google_url": _google_url(barcode, name), "note": None,
    }
    if not barcode:
        out["note"] = "no_barcode"      # nothing to auto-resolve — hand back the Google (name) link
        return out

    async with httpx.AsyncClient(timeout=_TIMEOUT, headers={"User-Agent": "Banco/1.0"}) as c:
        # 1) UPCitemdb trial — rich + rate-limited. Read the quota straight off the headers.
        try:
            r = await c.get(_UPCITEMDB_TRIAL, params={"upc": barcode})
            rem = r.headers.get("x-ratelimit-remaining")
            if rem is not None:
                out["quota"] = {
                    "remaining": int(rem),
                    "limit": int(r.headers.get("x-ratelimit-limit") or 0),
                    "reset": int(r.headers.get("x-ratelimit-reset") or 0),
                    "source": "upcitemdb",
                }
            if r.status_code == 200:
                items = (r.json() or {}).get("items") or []
                if items:
                    it = items[0]
                    out.update(
                        found=True, source="upcitemdb",
                        title=it.get("title") or None, brand=it.get("brand") or None,
                        category=it.get("category") or None,
                        description=it.get("description") or None,
                        images=[u for u in (it.get("images") or []) if u][:6],
                    )
                    return out
            elif r.status_code == 429:
                out["note"] = "quota_exhausted"     # over the free daily limit → fall through to OPF
        except Exception:
            pass

        # 2) Open Products Facts — free + unlimited; coverage + LANGUAGE vary (flag it, don't trust).
        try:
            r2 = await c.get(_OPF.format(barcode))
            d2 = r2.json() or {}
            if d2.get("status") == 1:
                p = d2.get("product") or {}
                imgs = [p.get("image_url")] if p.get("image_url") else []
                out.update(
                    found=True, source="openproductsfacts",
                    title=out["title"] or p.get("product_name") or None,
                    brand=out["brand"] or p.get("brands") or None,
                    category=out["category"] or p.get("categories") or None,
                    description=out["description"] or p.get("generic_name") or None,
                    images=out["images"] or [u for u in imgs if u],
                )
                langs = p.get("languages_hierarchy") or []
                if langs:
                    out["lang_hint"] = str(langs[0]).replace("en:", "")   # e.g. 'nl' → Dutch
                return out
        except Exception:
            pass

    if out["note"] is None:
        out["note"] = "not_found"
    return out
