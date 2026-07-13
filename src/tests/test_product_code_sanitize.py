"""Barcode-box trap backstop — a NAME must never become a product's barcode or its
immutable SKU.

The trap (found onboarding Ecolution, 2026-07-13): the receiving screen's box says
"scan or type a barcode", so a new hire types the product NAME there. Client-side that
name became the barcode, and 'LZ-'+name became the SKU — baked in forever (SKU is
immutable) and printed as the postcard serial. _sanitize_product_codes is the server
backstop protecting every create path, not just the receiving screen.
"""
from src.routes.pos_router import _sanitize_product_codes


def test_name_shaped_sku_is_replaced_with_clean_minted_code():
    out = _sanitize_product_codes({
        "sku": "Deluxe Wool Glasses Case — Merino Felt (Gray)",
        "barcode": "Deluxe Wool Glasses Case — Merino Felt (Gray)",
        "name": "Deluxe Wool Glasses Case",
    })
    # A name has spaces → not a code. Barcode dropped, SKU minted clean.
    assert out["barcode"] is None
    assert out["sku"].startswith("LZ-")
    assert " " not in out["sku"]
    assert out["sku"] != "Deluxe Wool Glasses Case — Merino Felt (Gray)"


def test_real_codes_pass_through_untouched():
    out = _sanitize_product_codes({"sku": "ECO-0001", "barcode": "7610000123463"})
    assert out["sku"] == "ECO-0001"
    assert out["barcode"] == "7610000123463"


def test_empty_or_missing_sku_is_minted():
    out = _sanitize_product_codes({"sku": "", "barcode": None})
    assert out["sku"].startswith("LZ-")
    assert out["barcode"] is None


def test_barcode_with_spaces_is_dropped_but_valid_sku_kept():
    out = _sanitize_product_codes({"sku": "TAM-25967", "barcode": "not a real code"})
    assert out["sku"] == "TAM-25967"          # a real code survives
    assert out["barcode"] is None             # the name-shaped 'barcode' is dropped


def test_minted_skus_are_unique_per_call():
    a = _sanitize_product_codes({"sku": "has a space"})["sku"]
    b = _sanitize_product_codes({"sku": "has a space"})["sku"]
    assert a != b
