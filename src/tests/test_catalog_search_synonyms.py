"""BL-101 durable layer — bilingual/brand search-term expansion.

The till catalog is stored in German; people ask in English or by brand. These lock the
cross-language bridge (the whole reason the layer exists) and the safety property that an
unrecognised query expands to nothing (so the plain search runs unchanged).
"""
from src.services.catalog_search_synonyms import expand_search_terms, SYNONYM_CONCEPTS


def test_english_lighter_reaches_german_category():
    got = expand_search_terms("lighter")
    assert "feuerzeug" in got and "feuerzeuge" in got


def test_multiword_query_still_expands_via_token():
    # "bic lighter" — the brand word has no concept, but the "lighter" token still fires.
    got = expand_search_terms("bic lighter")
    assert "feuerzeug" in got


def test_scale_and_grinder_and_ashtray_and_pipe():
    assert "waagen" in expand_search_terms("scale")
    assert "mühle" in expand_search_terms("grinder")
    assert "aschenbecher" in expand_search_terms("ashtray")
    assert "pfeifen" in expand_search_terms("pipe")


def test_bridge_is_bidirectional_german_to_english():
    # a German ask should also reach the English term (English lives in descriptions).
    assert "lighter" in expand_search_terms("feuerzeug")


def test_multiword_concept_key_matches_as_phrase():
    # "rolling paper" is a phrase concept-key, not a single token.
    got = expand_search_terms("rolling paper")
    assert "drehpapier" in got


def test_unknown_query_expands_to_nothing():
    # the safety net: no concept → [] → caller runs the plain search unchanged.
    assert expand_search_terms("bic") == []          # brand-only, no concept row
    assert expand_search_terms("xyzzy zzz") == []
    assert expand_search_terms("") == []
    assert expand_search_terms("   ") == []


def test_overlong_query_is_ignored():
    assert expand_search_terms("lighter " * 20) == []


def test_expansion_includes_own_concept_terms_for_category_match():
    # we deliberately KEEP the query's own term (base search never checks category, so the
    # category-boost needs "feuerzeug"/"feuerzeuge" present even when q was "feuerzeuge").
    got = expand_search_terms("feuerzeuge")
    assert "feuerzeuge" in got


def test_no_concept_is_empty_or_singleton():
    # every concept must offer a real bridge — a lone term expands to nothing useful.
    for group in SYNONYM_CONCEPTS:
        assert len(group) >= 2, f"concept {group} has no synonym to bridge to"
