"""BL-131 — a pasted product-page URL must yield the product's picture, with no manual upload.

The operator's workflow ends with a browser tab open on the right page. Making them right-click →
save → upload is the donkey-work this deletes: paste the URL in the sheet's Source URL column and the
import pulls the picture itself. These lock the extraction rules (network calls are not made here —
the live fetch is proven against the real cbdoilshop.gr page on sandbox).
"""
import pytest

from src.routes.pos_router import _page_main_image


@pytest.mark.asyncio
async def test_rejects_non_http():
    for u in ("", None, "not a url", "ftp://x/y.jpg", "javascript:alert(1)", "file:///etc/passwd"):
        assert await _page_main_image(u) is None


@pytest.mark.asyncio
async def test_direct_image_urls_are_taken_as_is():
    """An operator pastes whatever they were looking at — half the time that's the IMAGE, not the page
    (right-click → copy image address, or straight out of Google Images). Both are legitimate answers
    to 'where is this product's picture'. No network needed: the extension is proof enough."""
    for u in ("https://lasalade.ch/1517-large_default/ol-cbd-10-bio.jpg",
              "https://x.ch/a.PNG",
              "https://greenpassion.ch/cdn/shop/files/hash.png?v=1746001808&width=640",
              "https://x.ch/a.webp"):
        assert await _page_main_image(u) == u
