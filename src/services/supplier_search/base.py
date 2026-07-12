"""Live supplier-site search — shared types + HTTP/parse helpers.

When the local catalog + reference cache MISS a product Felix is holding, we search the
supplier's OWN website live so the cashier can adopt a real product (name / price / photo /
EAN / tier prices) and we SELF-HEAL the reference table for next time. One adapter per
supplier (each site searches differently); every adapter returns a common ``SupplierResult``.

No new dependency: these supplier pages are stable server-rendered HTML (Magento etc.), so
we parse with tight regexes rather than pulling in a soup library the app image lacks.
"""
from __future__ import annotations

import difflib
import html as _html
import re
from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

import httpx

_CENT = Decimal("0.01")

# A real desktop UA — some shops WAF-block obvious bots on their AJAX/search endpoints.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def money2(v) -> str:
    """Quantize to a 2dp money STRING (matches products.price_tiers storage)."""
    return f"{Decimal(str(v)).quantize(_CENT, rounding=ROUND_HALF_UP)}"


def parse_chf(text) -> Optional[float]:
    """Parse a Swiss price string to a float. Handles ``CHF 6.90``, ``CHF 39.–`` /
    ``39.-`` (dash cents = .00), and the ``1'234.50`` thousands apostrophe."""
    if text is None:
        return None
    s = str(text).upper().replace("CHF", "").replace("'", "").replace("–", "-").strip()
    m = re.match(r"\s*(\d+)(?:[.,](\d{1,2}|-))?", s)
    if not m:
        return None
    whole, frac = m.group(1), m.group(2)
    cents = 0 if frac in (None, "-", "") else int(frac.ljust(2, "0")[:2])
    return float(f"{whole}.{cents:02d}")


def clean_text(s: Optional[str], limit: Optional[int] = None) -> str:
    """Strip tags + collapse whitespace + unescape HTML entities."""
    s = _html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] if limit else s


def score_title(query: str, title: str) -> float:
    """Cheap relevance 0..1 of a result title vs the query (for ranking across suppliers)."""
    q = (query or "").lower().strip()
    t = (title or "").lower()
    if not q or not t:
        return 0.0
    ratio = difflib.SequenceMatcher(None, q, t).ratio()
    if q in t:                       # substring hit — strong signal difflib undersells
        ratio = max(ratio, 0.75)
    return round(ratio, 3)


def make_client(timeout: float = 15.0) -> httpx.AsyncClient:
    """A browser-shaped async client with a cookie jar (some Magento search needs a session)."""
    return httpx.AsyncClient(
        headers={
            "User-Agent": BROWSER_UA,
            "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=timeout,
        follow_redirects=True,
    )


@dataclass
class SupplierResult:
    """One adoptable product found live on a supplier site. Shaped so the find-first picker
    can render + adopt it exactly like a reference-catalog row, plus ``is_live`` for the badge
    and ``price_tiers`` so a quantity ladder rides along."""

    supplier: str
    title: str
    product_url: str
    price: Optional[float] = None
    currency: str = "CHF"
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_tiers: list = field(default_factory=list)   # [{"min_qty": int, "unit_price": "4.00"}]
    tier_mode: str = "per_unit"
    score: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["name"] = self.title            # the picker template reads `name`
        d["title"] = self.title
        d["suggested_price"] = self.price  # reference rows carry `suggested_price`
        d["is_reference"] = True           # reuse the adopt-from-reference path
        d["is_live"] = True                # ...but badge it "live from <supplier>"
        return d


class BaseAdapter:
    """One supplier site. ``search`` gets a shared client (cookies/session reused)."""

    supplier = "?"
    supplier_key = "?"

    async def search(self, client: httpx.AsyncClient, q: str, limit: int = 5) -> list[SupplierResult]:
        raise NotImplementedError
