"""BL-128 #2 — size-token boost regex (rank the exact size to the top of till search).

The query "lemon haze 2g" must float the 2g variant above the 10g. This locks the query→regex
extraction (digit-boundary safe: 2g never matches 12g/20g/2mg/2ml). The ORDER BY behaviour itself
was proven read-only on prod (Local Weed Lemon Haze 2g floats; 2ml/25gr do not).
"""
from src.routes.pos_router import _query_size_regex


def test_size_extracted_from_query():
    assert _query_size_regex("lemon haze 2g") == r"\y2\s?gr?\y"
    assert _query_size_regex("lemon haze 10g") == r"\y10\s?gr?\y"
    assert _query_size_regex("cbd oil 10ml") == r"\y10\s?ml\y"
    assert _query_size_regex("nicotine 20mg") == r"\y20\s?mg\y"


def test_no_size_no_boost():
    for q in ("grinder", "king size", "bic lighter", "", "lemon haze"):
        assert _query_size_regex(q) is None


def test_decimal_dot_escaped():
    # 0.5g → the decimal dot is escaped so the PG regex is literal, not any-char
    assert _query_size_regex("hash 0.5g") == r"\y0\.5\s?gr?\y"
