"""The AI delivery-slip reader — the extraction coercion (BANCO-RECEIVING-GOODS-RECEIPT-SPEC).

Locks how the vision engine's raw JSON is shaped into clean line items: real lines kept, headers/
totals/junk dropped, quantities coerced, the DELIVERY_SLIP domain wired with the 1600px SLIP intake.
The live Gemini extraction is proven separately in sandbox on the slip-XX.png samples (the "4 examples").
"""
from src.services.vision import DELIVERY_SLIP, DOMAINS


def test_domain_registered_with_slip_intake():
    assert DOMAINS.get("delivery_slip") is DELIVERY_SLIP
    assert DELIVERY_SLIP.intake == "slip"          # 1600px, keeps small print legible


def test_coerce_keeps_real_lines_and_header():
    out = DELIVERY_SLIP.coerce({
        "supplier": "Tamar Trade GmbH", "delivery_note_no": "LS-2026-4471",
        "date": "2026-07-15", "confidence": 0.9,
        "lines": [
            {"description": "Gizeh King Size", "quantity": 20, "unit_price": 1.40},
            {"description": "Raw KS Classic", "quantity": "10", "unit_price": None},
        ],
    })
    assert out["supplier"] == "Tamar Trade GmbH"
    assert out["delivery_note_no"] == "LS-2026-4471"
    assert out["date"] == "2026-07-15"
    assert len(out["lines"]) == 2
    assert out["lines"][0] == {"description": "Gizeh King Size", "quantity": 20.0, "unit_price": 1.40}
    assert out["lines"][1]["quantity"] == 10.0            # string coerced
    assert out["lines"][1]["unit_price"] is None


def test_coerce_drops_junk_and_defaults_quantity():
    out = DELIVERY_SLIP.coerce({"lines": [
        {"description": "", "quantity": 1},               # no description → dropped
        "not-a-dict",                                     # not an object → dropped
        {"description": "Old School Papers"},             # missing qty → defaults to 1
        {"description": "Filter", "quantity": 0},         # zero/invalid qty → 1
    ]})
    descs = [l["description"] for l in out["lines"]]
    assert descs == ["Old School Papers", "Filter"]
    assert all(l["quantity"] == 1 for l in out["lines"])


def test_coerce_handles_empty_and_missing_lines():
    assert DELIVERY_SLIP.coerce({})["lines"] == []
    assert DELIVERY_SLIP.coerce({"lines": None})["lines"] == []
    blank = DELIVERY_SLIP.coerce({})
    assert blank["supplier"] == "" and blank["confidence"] == 0.0
