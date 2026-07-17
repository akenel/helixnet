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
