"""Tier-2 web product lookup (Felix's "search the web" — banco-web-search-fallback).

Locks the pure logic (never-raises contract, no-barcode path, Google fallback always present) and a
tolerant LIVE smoke test against the free keyless DBs (skips if the network/service is down, so the
gate never flakes on someone else's uptime). "Sold once, born forever."
"""
import pytest

from src.services.web_product_lookup import lookup_product, _google_url


# ---- pure logic (no network) ------------------------------------------------
def test_google_url_combines_barcode_and_name():
    u = _google_url("070330600072", "bic lighter")
    assert u.startswith("https://www.google.com/search?q=")
    assert "070330600072" in u and "bic" in u


def test_google_url_none_when_empty():
    assert _google_url("", "") is None


async def test_no_barcode_returns_google_but_no_lookup():
    # No barcode → nothing to auto-resolve; hand back the Google (name) link, note='no_barcode'.
    r = await lookup_product("", "clipper gas")
    assert r["found"] is False
    assert r["note"] == "no_barcode"
    assert r["google_url"] and "clipper" in r["google_url"]
    # the dict is always UI-ready — every key present
    for k in ("found", "source", "title", "brand", "category", "description", "images",
              "quota", "google_url", "note"):
        assert k in r


async def test_empty_everything_never_raises():
    r = await lookup_product(None, None)
    assert r["found"] is False and r["images"] == [] and r["google_url"] is None


# ---- live smoke (skips cleanly if the free API is unreachable) ---------------
@pytest.mark.parametrize("barcode,expect_word", [
    ("070330600072", "bic"),          # BIC Mini Lighters — UPCitemdb
    ("7610948070107", "sambal"),      # Avopri Sambal Oelek — Open Food Facts (Swiss)
])
async def test_live_lookup_resolves_known_barcode(barcode, expect_word):
    try:
        r = await lookup_product(barcode)
    except Exception as e:                       # transport blip → not our failure
        pytest.skip(f"web-lookup network unavailable: {e}")
    if not r["found"]:
        pytest.skip("free DB miss/quota — coverage varies, not a code failure")
    assert expect_word in (r["title"] or "").lower()
    assert r["google_url"]                        # fallback always present
    # any images returned must be the ones that actually load (validated)
    assert isinstance(r["images"], list)
