"""BL-130 — the shelf-photo reader's vocabulary must land on the canonical tree.

Reading the shop from photos invented its own plain-English category names ("Bong Accessories &
Cleaning", "Growing Supplies", "Incense"). They are NOT our canonical labels, so a seeded batch
dumped ~half its rows into "Unsorted". These lock the synonym map at the funnel chokepoint so a
future photo-read batch can't strand itself again (same doctrine as the German-slug mess: fix the
funnel, not the rows).
"""
import pytest

from src.services.catalog_taxonomy import canonicalize_category

# every category label the 47-photo read produced (2026-07-16)
PHOTO_READ_LABELS = [
    "Rolling Papers", "Filters & Tips", "Pre-Rolled Cones", "Rolling Machines",
    "Rolling Trays & Mats", "Blunt Wraps & Cigarillos", "Vaporizers", "Vapes & E-Liquids",
    "Bongs & Water Pipes", "Pipes", "Bong Accessories & Cleaning", "Grinders",
    "Storage & Stash", "Scales", "Lighters", "CBD & Hemp", "Tobacco", "Tobacco Substitutes",
    "Incense", "Smudge & Ritual", "Aromatherapy & Room Spray", "Cosmetics & Body Care",
    "Humidity Control", "Growing Supplies", "Books & Media", "Games", "Jewelry & Decor",
    "Detox & Test Kits", "Accessories",
]


@pytest.mark.parametrize("label", PHOTO_READ_LABELS)
def test_every_photoread_label_is_canonical(label):
    cat, group = canonicalize_category(label)
    assert cat != "Unsorted", f"{label!r} strands in Unsorted"
    assert group != "Unsorted / System" or cat == "Accessories (general)"


def test_specific_mappings():
    assert canonicalize_category("Bong Accessories & Cleaning")[0] == "Bong & Pipe Accessories"
    assert canonicalize_category("Growing Supplies") == ("Grow Supplies", "Grow & Lab")
    assert canonicalize_category("Incense")[0] == "Incense & Smudge"
    assert canonicalize_category("Detox & Test Kits")[0] == "Drug Testing"


def test_mixed_vape_bucket_refines_by_name():
    # one source heading, three real lanes — the NAME is the tell
    assert canonicalize_category("Vapes & E-Liquids", "Elf Bar 600 Disposable")[0] == "Prefilled & Disposables"
    assert canonicalize_category("Vapes & E-Liquids", "Elfa Pro Prefilled Pods 2-Pack")[0] == "Coils & Pods"
    assert canonicalize_category("Vapes & E-Liquids", "Innokin Endura T18 Kit")[0] == "Vape Devices"
    assert canonicalize_category("Vapes & E-Liquids", "ELFLIQ Nic Salt Mango 10ml")[0] == "E-Liquids"


def test_name_is_optional_and_unknown_still_unsorted():
    # callers that pass no name behave exactly as before
    assert canonicalize_category("Vapes & E-Liquids")[0] == "E-Liquids"
    assert canonicalize_category("Some Invented Category")[0] == "Unsorted"
    assert canonicalize_category("")[0] == "Unsorted"


# --- BL-134: the FourTwenty supplier catalog's own headings (10,284 reference rows) ---

FOURTWENTY_LABELS = [
    "CBD & Hemp", "Grinders", "Pipes & Bongs", "Lighters", "Merch", "Grow Supplies", "Other",
    "Accessories", "Vaporizers", "E-Liquids", "Creams & Topicals", "Papers & Filters",
    "Tobacco & Cigarettes", "Edibles",
]


@pytest.mark.parametrize("label", FOURTWENTY_LABELS)
def test_every_fourtwenty_label_lands(label):
    cat, _ = canonicalize_category(label)
    assert cat != "Unsorted", f"FourTwenty's {label!r} strands — those rows can't round-trip"


def test_papers_and_filters_splits_by_name():
    """The silently WRONG one: 'Papers & Filters' sent every FILTER into Rolling Papers (772 rows)."""
    assert canonicalize_category("Papers & Filters", "RAW Classic Papers")[0] == "Rolling Papers"
    assert canonicalize_category("Papers & Filters", "PURIZE Xtra Slim Aktivkohlefilter 50 Stk")[0] == "Filters & Tips"
    assert canonicalize_category("Papers & Filters", "GIZEH 200 Procell Green 6mm")[0] == "Filters & Tips"
    assert canonicalize_category("Papers & Filters", "Mascotte Filter Tips")[0] == "Filters & Tips"


def test_pipes_and_bongs_splits_by_name():
    """A hand pipe, a bong, and a bong PART are three different things under one supplier heading —
    the exact confusion a 'Chillum' search surfaces (hand pipe vs 18.8 downstem)."""
    assert canonicalize_category("Pipes & Bongs", "Chillum Glas bunt 10cm")[0] == "Pipes"
    assert canonicalize_category("Pipes & Bongs", "Acryl Bong zylindrisch 600mm")[0] == "Bongs"
    assert canonicalize_category("Pipes & Bongs", "Glas Adapterchillum 14.5 21cm")[0] == "Bong & Pipe Accessories"


def test_mixed_refine_needs_a_name_and_is_safe_without_one():
    # no name → the base label, never a guess
    assert canonicalize_category("Papers & Filters")[0] == "Rolling Papers"
    assert canonicalize_category("Pipes & Bongs")[0] == "Pipes"
