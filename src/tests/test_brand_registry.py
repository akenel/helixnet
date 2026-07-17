"""BL-132 — brand-first + official-site scoping. The metadata that makes a search land on the real pack."""
from src.services.brand_registry import (BRAND_SITES, detect_brand, image_query,
                                         official_site, search_query)


def test_detects_brand_in_name():
    assert detect_brand("Gizeh King Size Slim Extra Fine Black 34") == "GIZEH"
    assert detect_brand("RAW Classic King Size Slim") == "RAW"
    assert detect_brand("Purize Xtra Slim Filters 50") == "Purize"
    assert detect_brand("Alda small 76mm") is None


def test_word_boundaries():
    # 'RAW' must not fire inside 'drawer'; 'PAX' must not fire inside 'paxton'
    assert detect_brand("Wooden drawer box") is None
    assert detect_brand("Paxton grinder") is None


def test_longest_brand_wins():
    # "Lost Mary" must beat a bare "Mary"; "Green Passion" must beat "Green"
    assert detect_brand("Lost Mary BM600 Blueberry") == "Lost Mary"
    assert detect_brand("Green Passion Charas") == "Green Passion"


def test_brand_first_query():
    assert search_query("Classic King Size Slim") == "Classic King Size Slim"      # no brand → unchanged
    assert search_query("Zippo Windproof") == "Zippo Windproof"                    # already leads → unchanged
    assert search_query("Blue Rolls by Smoking").startswith("Smoking ")            # brand hoisted to front


def test_image_query_scopes_to_official_site_only_when_known():
    assert "site:gizeh.com" in image_query("Gizeh King Size Slim")
    assert "site:" not in image_query("Alda small 76mm")


def test_no_parked_or_reseller_domains():
    """A 200 does not mean it's the brand: ocbpapers.com/golokaincense.com are HugeDomains parking
    pages, elfbar.com redirects to a reseller. A WRONG official site costs a wrong picture."""
    bad = ("hugedomains", "instavape", "smart-smoking")
    for brand, dom in BRAND_SITES.items():
        assert not any(b in dom for b in bad), f"{brand} points at {dom}"
        assert "/" not in dom and " " not in dom, f"{brand}: {dom} is not a bare domain"


def test_official_site_none_for_unknown():
    assert official_site(None) is None
    assert official_site("Nonexistent Brand") is None
