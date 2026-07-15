"""The living-catalogue product page helpers (BANCO-PRODUCT-PAGE-SPEC phase 1).

Locks the pure render helpers: the spec table (attributes → labelled rows), the tier ladder
(price_tiers → base + break rows with save%), and the breadcrumb (parse the Artemis path tag).
"""
from src.routes.pos_router import (
    _product_page_specs, _product_page_tiers, _product_breadcrumb, _spec_label,
)


# ---- spec table -------------------------------------------------------------
def test_specs_prettify_known_keys_and_localize():
    attrs = {"raw_material": "Wood", "papierst_rke": "13 gr/m²", "brand": "Greengo"}
    rows = dict(_product_page_specs(attrs, "en"))
    assert rows["Material"] == "Wood"
    assert rows["Paper weight"] == "13 gr/m²"
    assert rows["Brand"] == "Greengo"
    # German label for the same key
    assert _spec_label("papierst_rke", "de") == "Papierstärke"


def test_specs_skip_blanks_and_internal_keys():
    attrs = {"brand": "X", "confidence": "0.9", "source_lang": "en", "size": "", "width": None}
    rows = dict(_product_page_specs(attrs, "en"))
    assert "Brand" in rows
    assert "confidence" not in [k.lower() for k in rows] and "Size" not in rows and "Width" not in rows


def test_specs_unknown_key_is_titlecased():
    rows = dict(_product_page_specs({"some_field": "v"}, "en"))
    assert rows["Some Field"] == "v"


def test_specs_non_dict_is_empty():
    assert _product_page_specs(None, "en") == []
    assert _product_page_specs("nope", "en") == []


# ---- tier ladder ------------------------------------------------------------
def test_tiers_base_plus_breaks_with_save_pct():
    tiers = [{"min_qty": 1, "unit_price": 1.70}, {"min_qty": 10, "unit_price": 1.50},
             {"min_qty": 50, "unit_price": 1.00}]
    rows = _product_page_tiers(tiers, 1.70, "per_unit")
    assert rows[0] == {"qty": 1, "unit": "1.70", "save": 0}
    r10 = next(r for r in rows if r["qty"] == 10)
    assert r10["unit"] == "1.50" and r10["save"] == 12      # (1.70-1.50)/1.70 ≈ 12%
    r50 = next(r for r in rows if r["qty"] == 50)
    assert r50["save"] == 41                                # (1.70-1.00)/1.70 ≈ 41%


def test_tiers_empty_when_no_ladder():
    assert _product_page_tiers(None, 1.70, "per_unit") == []
    # a lone qty-1 row is not a ladder → nothing to show
    assert _product_page_tiers([{"min_qty": 1, "unit_price": 1.70}], 1.70, "per_unit") == []


def test_tiers_bundle_mode_per_unit_from_pack():
    # bundle "3 for 4.00" → per-unit 1.333… shown at qty 3
    rows = _product_page_tiers([{"min_qty": 3, "unit_price": 4.00}], 2.00, "bundle")
    r3 = next(r for r in rows if r["qty"] == 3)
    assert r3["unit"] == "1.33"


# ---- breadcrumb -------------------------------------------------------------
def test_breadcrumb_parses_artemis_path_tag():
    crumbs = _product_breadcrumb("artemis:papers-co/drehpapier/greengo,brand:Greengo", "Rolling Papers")
    assert crumbs == ["Papers Co", "Drehpapier", "Greengo"]


def test_breadcrumb_falls_back_to_category():
    assert _product_breadcrumb("brand:X", "Rolling Papers") == ["Rolling Papers"]
    assert _product_breadcrumb(None, None) == []
