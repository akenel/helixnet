"""
THE Day-One replay — the golden path, API level (`day-one-first-sale`).

Mirrors the demo/test sheet (docs/testing/banco/BANCO-DAY-ONE-TEST-SHEET.html): an item
with NO barcode is born once, sold, and **found by name on the very next sale** — with the
stock count never moving (zero perpetual inventory). If this stays green, the Day-One spine
is alive and can't silently regress before Felix sees it.

Scope: this locks the BACK-END contract the fixed UI must call. The front-end
"Catalog Mode -> [CATALOG] one-off line" bug (docs/BANCO-BORN-ONCE-NO-BARCODE-FIX.md) is a
UI routing bug caught by the Playwright/manual phone pass, not here.
"""
import uuid
from decimal import Decimal

from conftest import POS, ring_sale


def _born_once_no_barcode(session, name, price):
    """The "new item, no barcode" born-once create = POST /products with barcode=null.
    This is what the fixed UI must do instead of pushing a throwaway [CATALOG] line."""
    r = session.post(f"{POS}/products", json={
        "sku": "LZ-" + uuid.uuid4().hex[:10],
        "barcode": None,
        "name": name,
        "price": str(price),
    })
    r.raise_for_status()
    return r.json()


def _search_by_name(session, q):
    r = session.get(f"{POS}/search", params={"q": q, "limit": 50})
    r.raise_for_status()
    return r.json().get("items", [])


def _stock(session, pid):
    return session.get(f"{POS}/products/{pid}").json().get("stock_quantity")


def test_day_one_first_sale_golden_path(session):
    # Unique name so the run is deterministic on the shared/sandbox DB; we still assert by
    # exact id, so any other "black cup" rows can't make this pass falsely.
    name = "TEST black cup " + uuid.uuid4().hex[:6]

    # --- Beats 2/3: born once, NO barcode -> a REAL product (not a one-off line) ---
    prod = _born_once_no_barcode(session, name, "15.00")
    pid = prod.get("id")
    assert pid, "born-once must return a real product with an id"
    assert prod.get("barcode") in (None, ""), "this item genuinely has no barcode"
    assert prod.get("is_active") is True, "a born-once product must be sellable now"

    # --- Beat 7 (the whole promise): findable BY NAME, immediately ---
    hits = _search_by_name(session, "black cup")
    assert any(h.get("id") == pid for h in hits), \
        "a no-barcode born-once item MUST be findable by name (scan-once-known-forever)"

    before = _stock(session, pid)

    # --- Beat 5: the first sale ever, cash ---
    tx = ring_sale(session, [(pid, 1, Decimal("15.00"))],
                   payment_method="cash", amount_tendered=Decimal("20.00"))
    assert tx["status"] == "completed", "the first sale completes"

    # --- Zero perpetual inventory: the sale did NOT move the count ---
    after = _stock(session, pid)
    assert after == before, f"a sale must not move the count: {before} -> {after}"

    # --- Beat 7 again: the SECOND customer finds the same item by name (no re-entry) ---
    hits2 = _search_by_name(session, "black cup")
    assert any(h.get("id") == pid for h in hits2), \
        "the second customer's name search must still find it — not force a re-entry"
    tx2 = ring_sale(session, [(pid, 1, Decimal("15.00"))],
                    payment_method="cash", amount_tendered=Decimal("20.00"))
    assert tx2["status"] == "completed", "the second sale of the same item completes"
    assert tx2["id"] != tx["id"], "it's a distinct second transaction"
