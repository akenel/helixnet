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
