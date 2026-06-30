"""
Product search regression tests.

LOCKS the 2026-06-20 fix: the till's Search + Barcode modes were hitting
/products, which IGNORED the name/barcode params and returned the first N rows
no matter what you typed. Now Search uses the fuzzy /search (trigram) endpoint
and Barcode uses the exact /products/barcode/{bc} lookup.
"""
import pytest

from conftest import POS


def _items(session, **params):
    r = session.get(f"{POS}/search", params=params)
    r.raise_for_status()
    body = r.json()
    assert isinstance(body, dict) and "items" in body and "total" in body, f"envelope expected: {body}"
    return body


def test_search_finds_by_name(session):
    """Typing a distinctive name returns the matching product near the top."""
    body = _items(session, q="Alpine Dream", limit=10)
    assert body["items"], "fuzzy search returned nothing for 'Alpine Dream'"
    names = " ".join(p["name"].lower() for p in body["items"])
    assert "alpine" in names, f"expected the Alpine Dream flower in results: {names[:120]}"


def test_search_is_fuzzy_on_typo(session):
    """A typo ('grindr') still finds grinders -- proves trigram fuzziness, not substring."""
    body = _items(session, q="grindr", limit=5)
    assert body["items"], "fuzzy search returned nothing for the typo 'grindr'"
    assert any("grind" in p["name"].lower() for p in body["items"])


def test_search_results_carry_stock(session):
    """Search rows must include stock_quantity so the on-hand badges render."""
    body = _items(session, q="cbd", limit=5)
    assert body["items"]
    for p in body["items"]:
        assert "stock_quantity" in p


def test_search_term_actually_filters(session):
    """Two different terms must return DIFFERENT result sets."""
    a = {p["id"] for p in _items(session, q="grinder", limit=10)["items"]}
    b = {p["id"] for p in _items(session, q="lighter", limit=10)["items"]}
    assert a and b and a != b, "search returned identical results for different terms"


def test_search_paginates_with_honest_total(session):
    """total is the full match count; pages don't overlap and respect limit."""
    p1 = _items(session, q="cbd", limit=3, skip=0)
    assert p1["total"] >= 1
    assert len(p1["items"]) <= 3
    if p1["total"] > 3:
        p2 = _items(session, q="cbd", limit=3, skip=3)
        ids1 = {p["id"] for p in p1["items"]}
        ids2 = {p["id"] for p in p2["items"]}
        assert ids1.isdisjoint(ids2), "page 2 overlaps page 1"


def test_search_categories_endpoint(session):
    """The category list (for the filter) works -- the product_categories view exists."""
    r = session.get(f"{POS}/search/categories")
    assert r.status_code == 200, f"categories endpoint failed: {r.status_code}"
    cats = r.json()
    assert isinstance(cats, list)
    if cats:
        assert "name" in cats[0] and "count" in cats[0]
        # product_group drives the 2-level <optgroup> picker in the catalog filter;
        # it is always present (value may be null for ungrouped categories).
        assert "product_group" in cats[0]


def test_barcode_exact_lookup(session):
    """The dedicated barcode endpoint returns the EXACT product for a known barcode."""
    r = session.get(f"{POS}/products/barcode/7610000123461")  # 4-Piece Metal Grinder
    r.raise_for_status()
    p = r.json()
    assert p["barcode"] == "7610000123461"
    assert p["name"] == "4-Piece Metal Grinder"
