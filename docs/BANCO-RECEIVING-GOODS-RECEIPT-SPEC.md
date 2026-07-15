# Banco Receiving → Goods-Receipt & Maker Migration — Build Spec

*The receiving screen grows from "catalogue an item" into a proper, flexible **goods-receipt**
record — good enough that no one can say "it's missing the basics," light enough that we
haven't drowned it. It doubles as the **maker-migration** path (photograph a thing off a
website → a complete, sellable, labelable product). Felix gets new products all the time;
this is how they get in cleanly. Written 2026-07-15 from the design conversation with Angel.
All decisions below are Angel's calls. SANDBOX-first, always.*

Related: [[banco-ecolution-sylvie-supplier]] · [[banco-unsaved-work-guard]] ·
[[banco-photo-to-product-ai]] · [[banco-catalog-content-translation]] (description i18n) ·
[[banco-hardware-procurement]] (QL-820 label printer) · [[banco-closeout-timesheet-golive]]
(the daily summary) · BL-20 (sales-side Banana CSV — mirror it).

---

## 1. The vision

A craftsperson's item — or any supplier delivery — should come out the far end **complete,
sellable, labelable, and accounted for, in one pass.** Receiving is the accounting event
called **Wareneingang** (goods receipt) — the middle link in `PO → delivery note → goods
receipt → invoice → payment`. Capture the right metadata here and the payables side later is
almost free (the "three-way match": you never pay an invoice for goods that didn't arrive).

Two payoffs from one flow:
1. **Maker migration** — snap a photo → AI titles + describes it → priced, coded, labelled.
2. **Goods receipt** — a dated, attributed, per-supplier record that rolls into the daily
   summary and exports to Banana.

---

## 2. Two ways to receive (FLEXIBLE — Angel's refinement, decision A)

Do **not** hard-lock a whole session to one supplier. Support both, same screen:

- **Delivery-slip mode** — you pick a supplier (Sylvie/Ecolution), you're "writing her slip,"
  and every item you add **inherits that supplier by default** (fast for a real box delivery).
- **Individual mode** — each item can carry **its own supplier**, set per-item (the honest
  model: supplier is a property of the *product*, the session supplier is just a convenient
  default you can override on any line).

So: session supplier = a default, never a cage. The per-item supplier is what actually gets
stored on the product. This keeps the fast batch flow AND the "one-off, individual" flow Angel
realised he'll often want.

---

## 3. The born-great product record (per item)

**You + the AI provide (4 fields + a photo):**

| # | Field | Source | Notes |
|---|-------|--------|-------|
| 1 | Title | **AI reads the photo** — short, clean (not the SEO mouthful) | editable |
| 2 | **Description** | **AI writes it**, 1–2 clean sentences (decision F) | editable, can add more |
| 3 | Sale price | you type (the shelf price) | margin-checked (shipped) |
| 4 | Cost | auto from supplier trade-discount, or type | margin-checked |
| + | Photo | you upload → becomes the cover | done |

**The system mints automatically (the immutable identity — get it right ONCE):**

| Minted | Rule |
|--------|------|
| **SKU** | `PREFIX-####` sequential — §4 |
| **Internal barcode** | minted EAN-13, scannable + printable — §5 |
| **Label** | print-ready (barcode + QR) — §11 |

**Auto / no input needed:** supplier tag (§2), 18+ class (`resolve_class_on_create`, name-based
gate), VAT category (standard unless flagged), stock = 0 (zero-perpetual).

---

## 4. SKU & house prefix (decision A + B)

- SKU = **`PREFIX-####`**, sequential, **server-minted** (query max existing for that prefix,
  +1, zero-padded). Server-side so two people can't collide; a rare race → 409 → retry.
- `PREFIX` comes from the **supplier** picked for that item (Ecolution → `ECO`). Supplier
  prefix already exists on `SupplierModel.prefix` (2–3 uppercase letters, validated).
- **No supplier on an item?** Fall back to the shop's own **house/internal company code**, read
  from the **settings file** (`store_settings`), NOT hard-coded. Angel: candidates `PRODUCT-` /
  `ITEM-` — a company code, whatever the shop's is.
- **Reserved, never usable:** `ART` (collides with *article*/Artemis — confusing) and `LZ`
  (legacy lazy-create). Already enforced in `RESERVED_SUPPLIER_PREFIXES`.
- Today's `LZ-<timestamp>` mint is the thing we're replacing for supplier/maker items.

---

## 5. Internal barcode (EAN-13)

A no-barcode maker item needs a **scannable code** so it (a) rings at the till and (b) prints on
a label. Mint an **internal EAN-13** via the existing `mint_internal_ean13` helper
(`catalog_enrichment.py`), using a **private prefix range** so it can never collide with a real
manufacturer EAN. Minted at create time, stored on the product, immutable. This is the "generate
a barcode for it" ask — it's what makes the printed label useful at the counter.

---

## 6. AI description (decision F)

- AI writes a **short, clean 1–2 sentence** description in the **source language** it reads
  (EN/DE), stored as the source. It then flows to the other languages through the
  **`description_i18n`** map we already built (BL-36) — one good description → all languages.
- The operator can **edit / add more** if they want. Keep the AI title (short) over the
  supplier's long SEO title.

---

## 7. AI category (decision C)

AI **suggests** a category from the photo/title — but with a **visible "please check this"
nudge** to the user (don't blindly trust). If the operator ignores it, the suggestion stands;
they can re-file anytime. (Maker goods will often land in something like *Handmade / Accessories*.)

---

## 8. Goods-receipt metadata — the delivery header (decision 1 = Option 2)

Wrap each receiving session in an optional **delivery header** so it becomes a retrievable
*Wareneingang*, without building the full A/P engine:

| Header field | Why |
|--------------|-----|
| Supplier | default for the session (per-item overridable, §2) |
| **Delivery-note no.** (their Lieferschein ref) | later three-way match to their invoice |
| **Delivery date** (on their slip; may ≠ entry date) | correct period, audit |
| **Received-by** (staff) | automatic from login — accountability |
| Payment terms / on-account vs COD | the "credit info" — feeds payables later |
| **Attach the slip** (photo/PDF) | CH keeps business docs **10 yrs** (OR 958f); the scan *is* the record |

Per line: item, **quantity received** (optional; defaults 1 for a one-off), **unit cost**,
**line total**.

The full payables layer (link invoice → status `awaited → invoiced → paid`, QR-bill scan) is a
**LATER module** that merely *reads* this metadata. Not now.

---

## 9. Daily summary — "Goods received today" (Angel's home for it)

Receiving flows into the **daily summary / Felix's admin dashboard** as a **notice**, mirroring
the sales-side close:

- Headline: **"Today's arrivals — N items, CHF X total, entered by <staff>."** ← the *one big
  number* the Treuhänder wants.
- Grouped **by supplier**; expandable to line detail (item, qty, unit cost, line total, time,
  received-by, delivery-note no.).
- It's a *what-came-in-today* board, not an A/P screen. Who put it in the system, and what it was.

---

## 10. CSV → Banana export (Angel: "at least give them the option")

A **"Export goods received"** button on the daily summary → CSV, **reviewable and editable
before it exports** (Felix eyeballs it, fixes a cost, says "yep, that's exactly what came in").
Optional — there if wanted, invisible if not. Mirrors the sales-side Banana export.

**Columns (draft):** `date, supplier, delivery_note_no, item_name, sku, barcode, qty, unit_cost,
line_total, received_by`. Final Banana mapping = **Felix's Treuhänder's call**; we wire it.

---

## 11. Label print cockpit (decision E)

Not print-each-as-you-go. A **batch cockpit**:

- A queue of items **received but never printed** (a `label_printed_at` flag drives it).
- A **checklist** — tick which items to print, set **quantity of labels** per item (Angel: "qty
  needed").
- **Batch print** the selected set. One label size to start: **62 mm** (the QL-820 DK roll).
- Label content: **barcode** (till gun) **+ QR** (phone/postcard), title, price — one renderer,
  reusing the label/postcard engine (`generate_label.py`, BL-99).

---

## 12. Receiving previews — the happy moment (decision D)

Receiving should feel **beautiful, not clerical**. As an item is entered, show:
- the **postcard preview** (the maker card) — what it'll really look like,
- its **label preview**,
- and the **translations** (the description in the other languages).

"A beautiful, happy way to receive items — postcards, labels, previews — and not getting killed
right in the middle." This is the emotional payoff that makes migration a joy, not a chore.

---

## 13. Unsaved-work guard (status — [[banco-unsaved-work-guard]])

- ✅ **Desktop works great** (Angel confirmed): the New-item box won't vanish on a mis-tap /
  backdrop / ✕ without a "Discard this item?" confirm; the browser "Leave site?" guard catches
  the trackpad swipe-back.
- 🔜 **Mobile hardware/browser BACK button** — still to test on Angel's phone; if it still
  escapes, add the history/popstate barrier (needs on-device tuning). **The next test.**
- 🔜 Replicate the same guard to the scan/new-product screens (+ `suppressOnce()` before the
  legitimate scan→checkout hop).

---

## 14. Price/cost sanity (SHIPPED sandbox b1777)

Live margin line under the cost field (green "Margin CHF X (NN%)" / red "⚠ Below cost by CHF Y"),
and a confirm at save if cost > price. Catches the fat-finger before the item exists.

---

## 15. Build order (each → sandbox → Angel test)

1. ✅ Price validations
2. ✅ No-barcode photo-first + unsaved-work guard (desktop)
3. **Supplier-mode core** — per-item supplier (§2) + `PREFIX-####` SKU (§4) + internal EAN-13
   (§5) + supplier auto-tag. *The identity — do it first, get it right.*
4. **AI description** (§6) source → languages
5. **AI category suggestion + verify nudge** (§7)
6. **Delivery header + goods-receipt record** (§8)
7. **Daily "goods received" summary** (§9) + **CSV/Banana export** (§10)
8. **Label print cockpit** (§11)
9. **Receiving previews** — postcard + label + translations (§12)
10. Mobile back-button guard (§13) + partial barcode search (below)
11. Partial barcode search — type 3–4 digits → candidate matches (not full exact)

---

## 16. Out of scope (deliberately — "let's not overdo it")

Invoice matching / payment status (later A/P module) · VAT accrual on receiving (rides on the
invoice — Treuhänder) · full PO/ordering workflow (the Order Book already exists) · warehouse
bins / multi-location · serial/lot/expiry tracking · the variants/colours assortment model
(separate open question).

---

## 17. Open questions / where I stop and the Treuhänder starts

- **Tax calls are Felix's Treuhänder's**, not ours: no VAT on the delivery note (it's on the
  invoice); retention specifics; exact Banana creditor mapping. We wire what he says.
- **House prefix value** — confirm the shop's internal company code to store in settings.
- **Variants/colours** (a display box = ~8-colour assortment) — still the parked hard modelling
  question; not in this spec.
- **Future:** scan the CH **QR-bill** on the arriving invoice to auto-capture invoice + payment
  reference (the parked Swiss-QR scanner would finally earn its keep).
