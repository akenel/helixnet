"""Receiving supplier-mode identity — the minted SKU + internal barcode.

A no-barcode maker item gets a server-minted identity: SKU `PREFIX-####` (the supplier's own
prefix, else the shop house prefix) and a scannable internal EAN-13 seeded from that unique SKU.
The identity is immutable, so these lock the two pure pieces (EAN validity + uniqueness); the
DB-sequence + supplier-tag path is exercised live in the container.
"""
from src.services.catalog_enrichment import mint_internal_ean13, ean13_check_digit


def test_internal_ean_from_sku_is_a_valid_ean13():
    ean = mint_internal_ean13("ECO-0001")
    assert len(ean) == 13 and ean.isdigit()
    assert ean.startswith("20")                       # GS1 in-store / restricted range
    assert int(ean[-1]) == ean13_check_digit(ean[:12])  # check digit is correct


def test_different_skus_get_different_barcodes():
    # Each unique SKU seeds its own code — no two receiving items collide.
    assert mint_internal_ean13("ECO-0001") != mint_internal_ean13("ECO-0002")
    assert mint_internal_ean13("ITEM-0001") != mint_internal_ean13("ECO-0001")


def test_same_sku_is_deterministic():
    # Stable: re-minting the same SKU yields the same barcode (safe to recompute).
    assert mint_internal_ean13("ECO-0007") == mint_internal_ean13("ECO-0007")
