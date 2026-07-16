"""BL-129 — scanner-gun barcode hygiene.

A gun appends invisible junk (a trailing CR/LF/TAB "submit" signal) and a field that didn't clear
prepends the previous code. A dead-exact match then reads a KNOWN barcode as unknown → the operator
makes a duplicate, or binds the code to the wrong row. `_clean_barcode` scrubs to the bare code so
read == store. This is the tap root of "I scan the same code and it stops finding it."
"""
from src.routes.pos_router import _clean_barcode


def test_strips_trailing_submit_chars():
    for raw in ("42425700\r", "42425700\n", "42425700\r\n", "42425700\t", "42425700 "):
        assert _clean_barcode(raw) == "42425700"


def test_strips_leading_and_embedded_junk():
    assert _clean_barcode(" 42425700") == "42425700"
    assert _clean_barcode("\x0242425700") == "42425700"      # a stray control char (symbology prefix)
    assert _clean_barcode("424 25700") == "42425700"          # a gun that injected a space mid-code


def test_clean_code_untouched():
    assert _clean_barcode("42425700") == "42425700"
    assert _clean_barcode("7612400036195") == "7612400036195"


def test_empty_and_none():
    assert _clean_barcode("") == ""
    assert _clean_barcode(None) == ""
    assert _clean_barcode("   ") == ""
