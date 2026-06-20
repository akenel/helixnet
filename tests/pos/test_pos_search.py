"""
Product search regression tests.

LOCKS the 2026-06-20 fix: the till's Search + Barcode modes were hitting
/products, which IGNORED the name/barcode params and returned the first N rows
no matter what you typed. Now Search uses the fuzzy /search (trigram) endpoint
and Barcode uses the exact /products/barcode/{bc} lookup.
"""
import pytest

from conftest import POS


def test_search_finds_by_name(session):
    """Typing a distinctive name returns the matching product near the top."""
    r = session.get(f"{POS}/search", params={"q": "Alpine Dream", "limit": 10})
    r.raise_for_status()
    results = r.json()
    assert results, "fuzzy search returned nothing for 'Alpine Dream'"
    names = " ".join(p["name"].lower() for p in results)
    assert "alpine" in names, f"expected the Alpine Dream flower in results: {names[:120]}"


def test_search_is_fuzzy_on_typo(session):
    """A typo ('grindr') still finds grinders -- proves trigram fuzziness, not substring."""
    r = session.get(f"{POS}/search", params={"q": "grindr", "limit": 5})
    r.raise_for_status()
    results = r.json()
    assert results, "fuzzy search returned nothing for the typo 'grindr'"
    assert any("grind" in p["name"].lower() for p in results)


def test_search_results_carry_stock(session):
    """Search rows must include stock_quantity so the on-hand badges render."""
    r = session.get(f"{POS}/search", params={"q": "cbd", "limit": 5})
    r.raise_for_status()
    results = r.json()
    assert results
    for p in results:
        assert "stock_quantity" in p


def test_search_term_actually_filters(session):
    """Two different terms must return DIFFERENT result sets (the old bug returned
    the same first-N rows regardless of the term)."""
    a = session.get(f"{POS}/search", params={"q": "grinder", "limit": 10}).json()
    b = session.get(f"{POS}/search", params={"q": "lighter", "limit": 10}).json()
    a_ids = {p["id"] for p in a}
    b_ids = {p["id"] for p in b}
    assert a_ids and b_ids
    assert a_ids != b_ids, "search returned identical results for different terms (filter dead)"


def test_barcode_exact_lookup(session):
    """The dedicated barcode endpoint returns the EXACT product for a known barcode."""
    r = session.get(f"{POS}/products/barcode/7610000123461")  # 4-Piece Metal Grinder
    r.raise_for_status()
    p = r.json()
    assert p["barcode"] == "7610000123461"
    assert p["name"] == "4-Piece Metal Grinder"
