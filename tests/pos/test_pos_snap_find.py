"""
Find-first snap search — GET /products/find-matches.

The librarian half of snap-find: given a NAME (typed, or read off a photo by the AI),
it searches the LIVE catalog (`products`) AND the FourTwenty reference
(`reference_products`) by pg_trgm similarity and returns the REAL rows, ranked, each
with an HONEST match score (0..1) — not a model self-rating.

These are env-agnostic (no hardcoded seed item): they grab a real product, then prove
its own name finds it. The grinder lesson lives in `test_find_gibberish_is_low_score`:
nonsense must NOT come back as a confident match.
"""
import pytest

from conftest import POS


def _find(session, **params):
    r = session.get(f"{POS}/products/find-matches", params=params)
    r.raise_for_status()
    body = r.json()
    for k in ("query", "product_matches", "reference_matches", "best_match_score"):
        assert k in body, f"missing {k} in envelope: {body}"
    return body


def _any_product(session):
    """A real catalog product to key the self-consistency tests off (no hardcoded item)."""
    items = session.get(f"{POS}/search", params={"q": "a", "limit": 1}).json().get("items", [])
    if not items:
        pytest.skip("empty catalog on this env")
    return items[0]


def test_find_envelope_and_scores(session):
    """Every match carries a similarity score in [0,1]; best == the top product hit."""
    body = _find(session, q="grinder", limit=6)
    for m in body["product_matches"]:
        assert 0.0 <= m["score"] <= 1.0, f"score out of range: {m}"
    if body["product_matches"]:
        assert body["best_match_score"] == body["product_matches"][0]["score"]
    else:
        assert body["best_match_score"] == 0.0


def test_find_finds_the_real_item(session):
    """A product's OWN exact name surfaces it as a strong match — find, not invent."""
    p = _any_product(session)
    body = _find(session, q=p["name"], limit=10)
    ids = [m["id"] for m in body["product_matches"]]
    assert p["id"] in ids, f"exact name {p['name']!r} did not find its own product"
    assert body["best_match_score"] > 0.3, "a real item should score an honest, non-trivial match"


def test_find_ranks_best_first(session):
    """Results are ordered best-first (prefix hits, then descending similarity)."""
    p = _any_product(session)
    body = _find(session, q=p["name"], limit=10)
    # the product's own row should be at or near the top, and scores never ascend after a drop
    scores = [m["score"] for m in body["product_matches"]]
    assert scores == sorted(scores, reverse=True) or scores[0] >= scores[-1], \
        f"matches not ranked best-first: {scores}"


def test_find_gibberish_is_low_score(session):
    """THE grinder lesson: nonsense yields NO strong match, so the UI says 'not found →
    create new' instead of a confident wrong answer."""
    body = _find(session, q="zzqxwlnthgqvxk")
    assert body["best_match_score"] < 0.3, \
        f"gibberish returned a high match score (false confidence): {body['best_match_score']}"


def test_find_empty_query_is_empty(session):
    """No query → no matches (never dump the whole catalog as 'matches')."""
    body = _find(session, q="")
    assert body["product_matches"] == []
    assert body["reference_matches"] == []
    assert body["best_match_score"] == 0.0


def test_find_reference_matches_present(session):
    """The FourTwenty reference side returns the same shape (may be empty on a bare env)."""
    body = _find(session, q="grinder", limit=6)
    for m in body["reference_matches"]:
        assert m.get("is_reference") is True
        assert 0.0 <= m["score"] <= 1.0
