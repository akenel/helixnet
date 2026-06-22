# Banco — no-barcode item must be BORN ONCE, not a limbo line (bug + fix spec)

**Severity: demo-blocking.** Found by Angel in the sandbox, 2026-06-22. This breaks the
core promise ("scan once, known forever") for the ~50% of stock with no barcode — the
*most-sold* items (cups, papers). They become un-findable and get re-entered every sale.

---

## Root cause (confirmed in code)
Sale mode → **"Catalog Mode"** tab (labelled *"for items without barcodes"*) →
`addCatalogItem()` (`src/templates/pos/scan.html:848`) pushes a throwaway cart line:

```js
{ id: 'catalog-'+Date.now(), name: `[CATALOG] ${desc}`, price, isCatalogItem: true }
```

**It never `POST`s a product.** No catalog row is created. Same for the `[NEW]` fallback
line (`scan.html:775`). So:
- the item is **not in the catalog** → **not searchable by name** ("black cup" finds nothing)
- a second sale of the same item forces a **full re-entry**
- the `[CATALOG]` / `[NEW]` brackets are the tell: "this isn't a real product."

## Correct behaviour — born once, for no-barcode too
A no-barcode item entered in a sale must **create a REAL product** — same as a
scanned-not-on-file item, just without a manufacturer barcode:

- `POST /api/v1/pos/products` with `barcode: null`, auto SKU, a **generated internal code**
  (Code128/QR) → **label queue**, the **name**, **price**, and the **photo**.
- Add **that real product** to the cart (not a `[CATALOG]` line).
- Result: immediately **searchable by name**, scannable once the label prints, editable,
  and **duplicable** (black cup → red cup).

## The entry point
Replace / repurpose **"Catalog Mode"** with a **"New item — no barcode"** action that opens
the **same born-once modal** the scan-not-on-file path already uses (name · price · 📷 photo
· "make a label") — just with no pre-filled barcode. **One born-once modal, two ways in:**
a failed scan, or the "no barcode" button.

## Retire the limbo paths
- `addCatalogItem()` `[CATALOG]` one-off and the `[NEW]` fallback line must stop being the
  path for **real products**.
- Keep a true one-off line **only** for genuine non-catalog ad-hoc charges (a custom fee, a
  change-making treat) — clearly labelled as such, never for a sellable item.

## Acceptance
- [ ] In a sale, "new item, no barcode": type **black cup** + price + photo → **Add**.
- [ ] Cart shows **"black cup"** (no `[CATALOG]`/`[NEW]` bracket).
- [ ] Finish the sale.
- [ ] **Start a second sale → search "black cup" → it's THERE** and adds in one tap.
- [ ] It has an internal code in the **label queue**.
- [ ] (verify) product name-search returns freshly created **barcode-less, active** products
      — no filter should require a barcode.

## Nice-to-have (Angel's instinct — polish, not the core)
- Flag quick-captured items **"needs review / needs label"** (a tag or flag) so the back
  office can find and tidy them (fix name, print label, set category). `is_active`
  soft-delete already exists — **never hard-delete** (the photo + work stay).
- A **"duplicate"** action in the catalog (black cup → red cup): copy the row, change name +
  photo. Cheap once it's a real product.

---

*The fix is routing, not search: make the no-barcode item a real product at the moment of
sale, and everything downstream (name search, re-sell, duplicate, label) just works.*
